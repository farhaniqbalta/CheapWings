"""Durable verification work and append-only quote revisions; no adapter branching."""
from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

from pydantic import TypeAdapter
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from cheapwings.application.verification_service import shortlist
from cheapwings.domain.coverage import WorkStatus
from cheapwings.domain.evidence import ProviderFailure
from cheapwings.domain.itinerary import compute_fingerprint
from cheapwings.domain.offer import ComparisonStatus, Offer, PriceStatus, ThreeValued
from cheapwings.domain.segments import FlightSegment
from cheapwings.providers.base import ProviderSearchResult, RepriceRequest, SingleDateRouteQuery
from cheapwings.storage.db import write_session
from cheapwings.storage.models import (
    FareQuote,
    FXRow,
    ItineraryRow,
    QuoteRevision,
    SearchJob,
    SegmentRow,
    WorkItem,
)


def offer_from_row(row, *, private=False, data=None):
    return TypeAdapter(Offer).validate_python({**(data or row.canonical_json),
        'provider_quote_handle': row.provider_quote_handle_server_side if private else None})


class ResultsExpired(Exception):
    pass


class VerificationRepository:
    def schedule_verification(self):
        from cheapwings.storage.repository import ACTIVE, now_ms
        with write_session(self.engine) as s:
            for job in s.scalars(select(SearchJob).where(SearchJob.status.in_(('queued','running')))):
                if job.cancel_requested or not job.reprice_budget or not job.reprice_providers:
                    continue
                items = s.scalars(select(WorkItem).where(WorkItem.job_id == job.id)).all()
                if any(i.status in ACTIVE for i in items):
                    continue
                previous = [i for i in items if i.work_type == 'reprice']
                used = {i.target_key for i in previous}
                candidates = []
                for row in s.scalars(select(FareQuote).where(FareQuote.job_id == job.id)):
                    if str(row.id) in used or row.provider_id not in job.reprice_providers:
                        continue
                    offer = offer_from_row(row, private=True)
                    if offer.comparable_amount and offer.comparable_amount.currency == job.query_json['display_currency']:
                        candidates.append((row.id, offer))
                selected = shortlist(candidates, job.reprice_budget - len(previous))
                for key in selected:
                    row = s.get(FareQuote, key)
                    original = s.get(WorkItem, row.work_item_id)
                    if original is None:
                        continue
                    itin = s.get(ItineraryRow, row.itinerary_id)
                    if itin.identity_confidence != 'exact_segments':
                        continue  # cannot prove exact itinerary from a summary alone
                    s.add(WorkItem(id=str(uuid4()), job_id=job.id, provider_id=row.provider_id,
                        origin=original.origin, destination=original.destination,
                        departure_date=original.departure_date, work_type='reprice',
                        target_key=str(key), status='pending'))
                job.verification_planned = True
                job.phase = 'verifying'
                self.finalize(s, job, now_ms())

    def reprice_request(self, item):
        from datetime import date
        with Session(self.engine) as s:
            row = s.get(FareQuote, int(item.target_key))
            if row is None or row.job_id != item.job_id:
                raise ProviderFailure('unsupported_query')
            job = s.get(SearchJob, item.job_id)
            q = job.query_json
            segments = s.scalars(select(SegmentRow).where(
                SegmentRow.itinerary_id == row.itinerary_id).order_by(SegmentRow.ordinal)).all()
            return RepriceRequest(offer_from_row(row, private=True),
                tuple(TypeAdapter(FlightSegment).validate_python(seg.canonical_json) for seg in segments),
                SingleDateRouteQuery(item.origin, item.destination, date.fromisoformat(item.departure_date),
                    q['include_basic_economy'], q['include_hidden_city'], q['display_currency'],
                    q.get('point_of_sale_country')))

    @staticmethod
    def _revise(s, row, offer, reason, now):
        data = TypeAdapter(Offer).dump_python(replace(offer, provider_quote_handle=None), mode='json')
        data.pop('provider_quote_handle')
        row.canonical_json = data
        row.raw_amount_decimal_text = str(offer.amount_original.amount)
        row.raw_currency = offer.amount_original.currency
        row.comparable_amount_decimal_text = str(offer.comparable_amount.amount) if offer.comparable_amount else None
        row.comparable_currency = offer.comparable_amount.currency if offer.comparable_amount else None
        row.provider_quote_handle_server_side = offer.provider_quote_handle
        s.add(QuoteRevision(quote_id=row.id, revision_time=now,
            amount_decimal_text=row.raw_amount_decimal_text, currency=row.raw_currency,
            reason=reason, canonical_json=data))

    def _store_reprice(self, s, job, item, result, now):
        row = s.get(FareQuote, int(item.target_key))
        original = offer_from_row(row, private=True)
        segments = s.scalars(select(SegmentRow).where(
            SegmentRow.itinerary_id == row.itinerary_id).order_by(SegmentRow.ordinal)).all()
        expected = tuple(TypeAdapter(FlightSegment).validate_python(seg.canonical_json) for seg in segments)
        identity_matches = (bool(expected) and bool(result.segments) and
                            compute_fingerprint(expected) == compute_fingerprint(result.segments))
        if not result.available or not identity_matches or not result.offers:
            self._revise(s, row, replace(original,
                price_status=PriceStatus.CHANGED_OR_UNAVAILABLE, provider_quote_handle=None,
                warnings=original.warnings + ('Recheck unavailable or itinerary no longer matches.',)),
                'unavailable_or_identity_changed', now)
            job.verification_planned = False  # consider next candidates under remaining budget
            return
        # Adapter assertion is necessary but insufficient: independently compare known product fields.
        matching = [o for o in result.offers if (
            o.provider_id == original.provider_id and original.seller is not None
            and original.fare_family is not None and original.basic_economy is not None
            and (o.seller, o.fare_family, o.basic_economy, o.cabin, o.amount_original.currency)
                == (original.seller, original.fare_family, original.basic_economy,
                    original.cabin, original.amount_original.currency)
            and o.evidence and original.evidence
            and o.evidence.point_of_sale_country == original.evidence.point_of_sale_country)]
        if result.exact_product_match and len(matching) == 1:
            offer = matching[0]
            exact = (not offer.is_estimate and offer.hidden_city == ThreeValued.NO
                     and offer.comparison_status == ComparisonStatus.ELIGIBLE_TOTAL_KNOWN
                     and offer.comparable_amount is not None)
            offer = replace(offer, quote_id=original.quote_id, itinerary_id=row.itinerary_id,
                price_status=PriceStatus.REPRICED_EXACT if exact else
                             PriceStatus.INDICATIVE if offer.is_estimate else PriceStatus.RECENT_SEARCH,
                repriced_at=datetime.now(UTC) if exact else None)
            self._revise(s, row, offer, 'repriced_exact' if exact else 'checked_lower_confidence', now)
            return
        # Different/previously unknown seller or fare is a new distinct quote, never a badge on the old one.
        self._revise(s, row, replace(original, price_status=PriceStatus.CHANGED_OR_UNAVAILABLE,
                                    provider_quote_handle=None), 'replaced_by_distinct_seller_offers', now)
        query = self.reprice_query(job, item)
        new_offers = []
        for offer in result.offers:
            if offer.provider_id != row.provider_id:
                raise ProviderFailure('schema_changed')
            new_offers.append(replace(offer, provider_quote_handle=None, repriced_at=None,
                price_status=PriceStatus.INDICATIVE if offer.is_estimate else PriceStatus.RECENT_SEARCH))
        canonical = ProviderSearchResult(row.provider_id, query, WorkStatus.SUCCEEDED_RESULTS,
            datetime.now(UTC), None, None, None, (result.segments,), (tuple(new_offers),))
        self._store_results(s, job, item, canonical, now)
        job.verification_planned = False

    @staticmethod
    def reprice_query(job, item):
        from datetime import date
        q = job.query_json
        return SingleDateRouteQuery(item.origin, item.destination, date.fromisoformat(item.departure_date),
            q['include_basic_economy'], q['include_hidden_city'], q['display_currency'],
            q.get('point_of_sale_country'))

    def purge_expired(self, now=None):
        from cheapwings.storage.repository import now_ms
        now = now if now is not None else now_ms()
        with write_session(self.engine) as s:
            for job in s.scalars(select(SearchJob).where(SearchJob.data_expires_at <= now)):
                quotes = s.scalars(select(FareQuote).where(FareQuote.job_id == job.id)).all()
                ids = [q.id for q in quotes]
                fx_ids = [q.fx_snapshot_id for q in quotes if q.fx_snapshot_id is not None]
                s.execute(delete(QuoteRevision).where(QuoteRevision.quote_id.in_(ids)))
                s.execute(delete(FareQuote).where(FareQuote.id.in_(ids)))
                s.execute(delete(FXRow).where(FXRow.id.in_(fx_ids)))
                itins = select(ItineraryRow.id).where(ItineraryRow.job_id == job.id)
                s.execute(delete(SegmentRow).where(SegmentRow.itinerary_id.in_(itins)))
                s.execute(delete(ItineraryRow).where(ItineraryRow.job_id == job.id))
