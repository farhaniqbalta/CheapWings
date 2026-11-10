"""Canonical projections. No source-specific parsing or provider calls."""

import base64
import json
from collections import Counter
from datetime import UTC, datetime
from urllib.parse import urlsplit

from pydantic import TypeAdapter
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from cheapwings.application import contracts as dto
from cheapwings.domain.itinerary import (
    AirportTransfer,
    IdentityConfidence,
    Itinerary,
    ItinerarySummary,
)
from cheapwings.domain.offer import ComparisonStatus, LinkScope, Offer, PriceStatus
from cheapwings.domain.query import SearchQuery
from cheapwings.domain.segments import FlightSegment
from cheapwings.engine.expansion import expand_routes_and_dates
from cheapwings.engine.matching import ItineraryGroup
from cheapwings.engine.ranking import best_checked_deal, lowest_advertised
from cheapwings.storage.models import (
    FareQuote,
    ItineraryRow,
    QuoteRevision,
    SegmentRow,
    ProviderOperation,
    WorkItem,
)
from cheapwings.storage.repository import SUCCESS, now_ms
from cheapwings.storage.verification import ResultsExpired


def instant(ms):
    return datetime.fromtimestamp(ms / 1000, UTC) if ms is not None else None


def request_snapshot(data):
    data = dict(data)
    data.pop("max_combinations", None)
    data["passengers"] = {"adults": data.pop("adults")}
    stops = data.pop("max_stops")
    data["max_stops"] = None if stops == "any" else int(stops)
    return dto.SearchRequest.model_validate(data)


def status_projection(repo, job_id):
    job, items = repo.get_job(job_id)
    detailed = [i for i in items if i.work_type == "detailed"]
    reprices = [i for i in items if i.work_type == "reprice"]
    counts = Counter(i.status for i in detailed)
    providers = []
    for provider_id in sorted({i.provider_id for i in detailed}):
        entries = [i for i in detailed if i.provider_id == provider_id]
        pc = Counter(i.status for i in entries)
        providers.append(
            dto.ProviderProgress(
                provider_id=provider_id,
                succeeded=sum(pc[k] for k in SUCCESS),
                failed=pc["failed_terminal"],
                cancelled=pc["cancelled"],
                skipped_unsupported=pc["skipped_unsupported"],
                disabled_reason=next(
                    (i.last_error_detail for i in entries if i.status == "skipped_unsupported"),
                    None,
                ),
            )
        )
    warnings = ["Inventory completeness is unknown; coverage counts provider queries only."]
    if job.status in ("partial", "failed", "cancelled"):
        warnings.append("Search is incomplete; inspect provider coverage and errors.")
    if job.data_expires_at and job.data_expires_at <= now_ms():
        warnings.append("Live fare data expired and is no longer available; start a new search.")
    if any(i.unpriced_candidate_count for i in detailed):
        warnings.append(
            "Some source candidates had no price; see unpriced_candidate_count in coverage."
        )
    with Session(repo.engine) as session:
        operation_attempts = {
            i.operation_id: session.get(ProviderOperation, i.operation_id).attempts
            for i in items
            if i.operation_id
        }
    return dto.Job(
        provider_ids=job.provider_ids or [],
        cache_mode=job.cache_mode,
        exact_reprice_attempted=sum(i.attempts for i in reprices),
        exact_reprice_succeeded=_exact_reprice_count(repo, job_id),
        data_expires_at=instant(job.data_expires_at),
        job_id=job.id,
        query=request_snapshot(job.query_json),
        status=job.status,
        phase=job.phase,
        cancel_requested=job.cancel_requested,
        created_at=instant(job.created_at),
        updated_at=instant(job.updated_at),
        total_route_date_combinations=len(
            expand_routes_and_dates(SearchQuery.model_validate(job.query_json))
        ),
        covered_route_date_combinations=len(
            {(i.origin, i.destination, i.departure_date) for i in detailed if i.status in SUCCESS}
        ),
        total_provider_work_items=len(detailed),
        succeeded_provider_work_items=sum(counts[k] for k in SUCCESS),
        succeeded_empty=counts["succeeded_empty"],
        failed_provider_work_items=counts["failed_terminal"],
        skipped_unsupported=counts["skipped_unsupported"],
        cancelled_provider_work_items=counts["cancelled"],
        provider_status=providers,
        coverage=[
            dto.Coverage(
                result_origin=i.result_origin,
                observation_retrieved_at=instant(i.observation_retrieved_at),
                reused_at=instant(i.reused_at),
                cache_fresh_until=instant(i.cache_fresh_until),
                operation_attempts=operation_attempts.get(i.operation_id, 0),
                work_item_id=i.id,
                work_type=i.work_type,
                unpriced_candidate_count=i.unpriced_candidate_count,
                provider_id=i.provider_id,
                origin=i.origin,
                destination=i.destination,
                departure_date=i.departure_date,
                status=i.status,
                attempts=i.attempts,
                error_code=i.last_error_code,
                error_detail_sanitized=i.last_error_detail,
                result_count=i.result_count,
                provider_complete=i.provider_complete,
                started_at=instant(i.started_at),
                finished_at=instant(i.finished_at),
            )
            for i in items
        ],
        warnings=warnings,
    )


def _exact_reprice_count(repo, job_id):
    with Session(repo.engine) as s:
        return (
            s.scalar(
                select(func.count())
                .select_from(QuoteRevision)
                .join(FareQuote)
                .where(FareQuote.job_id == job_id, QuoteRevision.reason == "repriced_exact")
            )
            or 0
        )


def public_offer(offer, row_id, work=None):
    evidence_fields = {
        "result_origin",
        "reused_at",
        "fee_completeness",
        "source_checked_at",
        "point_of_sale_country",
        "attribution",
        "fx_rate",
        "fx_as_of",
    }
    data = {
        name: getattr(offer, name)
        for name in dto.PublicOffer.model_fields
        if name not in evidence_fields
        and name
        not in (
            "quote_id",
            "amount_original",
            "currency_original",
            "comparable_amount",
            "comparable_currency",
        )
    }
    evidence = offer.evidence
    fx = evidence.fx_snapshot if evidence else None
    data.update(
        fee_completeness=evidence.fee_completeness if evidence else "unknown",
        source_checked_at=evidence.source_checked_at if evidence else None,
        point_of_sale_country=evidence.point_of_sale_country if evidence else None,
        attribution=evidence.attribution if evidence else None,
        fx_rate=str(fx.rate) if fx else None,
        fx_as_of=fx.retrieved_at if fx else None,
    )
    # Only HTTP(S) external navigation is supported; userinfo and unsafe schemes rejected.
    try:
        link = urlsplit(offer.link or "")
        valid = link.scheme == "https" and link.hostname and not link.username and not link.password
    except ValueError:
        valid = False
    if not valid:
        data["link"], data["link_scope"] = None, LinkScope.UNAVAILABLE
    return dto.PublicOffer(
        **data,
        result_origin=work.result_origin if work else "live",
        reused_at=instant(work.reused_at) if work else None,
        quote_id=str(row_id),
        amount_original=str(offer.amount_original.amount),
        currency_original=offer.amount_original.currency,
        comparable_amount=(
            str(offer.comparable_amount.amount) if offer.comparable_amount else None
        ),
        comparable_currency=(offer.comparable_amount.currency if offer.comparable_amount else None),
    )


def results_projection(repo, job_id, sort, cursor=None, limit=50):
    job, _ = repo.get_job(job_id)
    if job.data_expires_at and job.data_expires_at <= now_ms():
        repo.purge_expired()
        raise ResultsExpired("Live fare data expired; start a new search")
    with Session(repo.engine) as s:
        maximum = s.scalar(select(func.max(FareQuote.id)).where(FareQuote.job_id == job_id)) or 0
        revision_cutoff = s.scalar(select(func.max(QuoteRevision.id))) or 0
        cutoff, offset, as_of = maximum, 0, now_ms()
        if cursor:
            try:
                payload = json.loads(base64.urlsafe_b64decode(cursor))
                cursor_job, cursor_sort, cutoff, offset, as_of, revision_cutoff = payload
                if (
                    cursor_job != job_id
                    or cursor_sort != sort
                    or any(
                        type(x) is not int or x < 0
                        for x in (cutoff, offset, as_of, revision_cutoff)
                    )
                    or cutoff > maximum
                ):
                    raise ValueError()
            except (ValueError, TypeError, UnicodeError):
                raise ValueError("Invalid results cursor") from None
        rows = s.scalars(
            select(FareQuote)
            .where(FareQuote.job_id == job_id, FareQuote.id <= cutoff)
            .order_by(FareQuote.id)
        ).all()
        groups, row_ids, work_rows = {}, {}, {}
        for row in rows:
            if row.itinerary_id not in groups:
                itin = s.get(ItineraryRow, row.itinerary_id)
                segments = s.scalars(
                    select(SegmentRow)
                    .where(SegmentRow.itinerary_id == itin.id)
                    .order_by(SegmentRow.ordinal)
                ).all()
                groups[itin.id] = ItineraryGroup(
                    Itinerary(
                        itinerary_id=itin.id,
                        segments=tuple(
                            TypeAdapter(FlightSegment).validate_python(seg.canonical_json)
                            for seg in segments
                        ),
                        identity_confidence=IdentityConfidence(itin.identity_confidence),
                        fingerprint=itin.fingerprint,
                        airport_transfers=TypeAdapter(tuple[AirportTransfer, ...]).validate_python(
                            itin.airport_transfers_json or []
                        ),
                        summary=TypeAdapter(ItinerarySummary).validate_python(itin.summary_json)
                        if itin.summary_json
                        else None,
                    )
                )
            revision = s.scalar(
                select(QuoteRevision)
                .where(QuoteRevision.quote_id == row.id, QuoteRevision.id <= revision_cutoff)
                .order_by(QuoteRevision.id.desc())
                .limit(1)
            )
            data = (
                revision.canonical_json
                if revision and revision.canonical_json
                else row.canonical_json
            )
            offer = TypeAdapter(Offer).validate_python(dict(data, provider_quote_handle=None))
            # Internal DB key disambiguates quote identifiers shared by different adapters.
            from dataclasses import replace

            offer = replace(offer, quote_id=str(row.id))
            groups[row.itinerary_id].offers.append(offer)
            row_ids[offer.quote_id] = row.id
            work_rows[offer.quote_id] = (
                s.get(WorkItem, row.work_item_id) if row.work_item_id else None
            )
        ranker = best_checked_deal if sort == "best_checked" else lowest_advertised
        # No cross-currency sorting without explicit FX; no stale/invalid or policy-ineligible fare.
        rank_groups = [
            ItineraryGroup(
                g.itinerary,
                [
                    o
                    for o in g.offers
                    if o.comparable_amount is not None
                    and o.comparable_amount.currency == job.query_json["display_currency"]
                    and o.price_status != PriceStatus.CHANGED_OR_UNAVAILABLE
                    and o.comparison_status != ComparisonStatus.INELIGIBLE
                ],
            )
            for g in groups.values()
        ]
        ranked = ranker(rank_groups)
        ordered, seen = [], set()
        for candidate in ranked:
            key = candidate.group.itinerary.itinerary_id
            if key in seen:
                continue
            seen.add(key)
            itin = candidate.group.itinerary
            ordered.append(
                dto.PublicItinerary(
                    itinerary_id=key,
                    warnings=list(itin.summary.warnings) if itin.summary else [],
                    identity_confidence=itin.identity_confidence,
                    carrier_names=list(itin.summary.carrier_names)
                    if itin.summary
                    else list(
                        dict.fromkeys(
                            segment.marketing_carrier_name or segment.marketing_carrier
                            for segment in itin.segments
                        )
                    ),
                    airport_transfers=[
                        dto.AirportTransfer(
                            after_segment=t.after_segment,
                            from_airport=t.from_airport,
                            to_airport=t.to_airport,
                        )
                        for t in itin.airport_transfers
                    ],
                    origin=itin.origin,
                    destination=itin.destination,
                    departure_local=itin.summary.depart_at
                    if itin.summary
                    else itin.segments[0].depart_at,
                    arrival_local=itin.summary.arrive_at
                    if itin.summary
                    else itin.segments[-1].arrive_at,
                    duration_minutes=itin.duration_minutes,
                    stops=itin.stops,
                    segments=[
                        dto.Segment(**TypeAdapter(FlightSegment).dump_python(seg))
                        for seg in itin.segments
                    ],
                    offers=[
                        public_offer(o, row_ids[o.quote_id], work_rows[o.quote_id])
                        for o in groups[key].offers
                    ],
                    ranked_quote_id=candidate.offer.quote_id,
                )
            )
        next_cursor = None
        if offset + limit < len(ordered):
            next_cursor = base64.urlsafe_b64encode(
                json.dumps([job_id, sort, cutoff, offset + limit, as_of, revision_cutoff]).encode()
            ).decode()
        return dto.Results(
            job_id=job_id,
            status=job.status,
            sort=sort,
            as_of=instant(as_of),
            next_cursor=next_cursor,
            itineraries=ordered[offset : offset + limit],
            warnings=["Prices may change. Inventory completeness is unknown."],
        )
