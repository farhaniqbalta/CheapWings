"""Short SQLite transactions. No provider I/O may occur inside a transaction."""

from collections import Counter
from time import time_ns
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from cheapwings.domain.query import SearchQuery
from cheapwings.engine.expansion import expand_routes_and_dates
from cheapwings.storage.db import write_session
from cheapwings.storage.models import SearchJob, WorkItem

ACTIVE = ("pending", "retry_wait", "running")
SUCCESS = ("succeeded_results", "succeeded_empty")
JOB_ACTIVE = ("queued", "running")


def now_ms():
    return time_ns() // 1_000_000


class CapacityExceeded(Exception):
    pass


class Repository:
    def __init__(self, engine):
        self.engine = engine

    def create_job(
        self, query: SearchQuery, registry, *, max_active=2, max_hourly=20, budget_seconds=1800
    ):
        now = now_ms()
        with write_session(self.engine) as s:
            jobs = s.scalars(select(SearchJob)).all()
            if (
                sum(j.status in JOB_ACTIVE for j in jobs) >= max_active
                or sum(j.created_at > now - 3_600_000 for j in jobs) >= max_hourly
            ):
                raise CapacityExceeded("Search creation budget exceeded; wait for capacity")
            job = SearchJob(
                id=str(uuid4()),
                query_json={
                    **query.model_dump(mode="json"),
                    "max_combinations": query.max_combinations,
                },
                created_at=now,
                updated_at=now,
                deadline_at=now + budget_seconds * 1000,
            )
            s.add(job)
            s.flush()
            for registration in registry:
                reason = registration.unavailable_reason
                for combo in expand_routes_and_dates(query):
                    s.add(
                        WorkItem(
                            id=str(uuid4()),
                            job_id=job.id,
                            provider_id=registration.provider.provider_id,
                            origin=combo.origin,
                            destination=combo.destination,
                            departure_date=combo.departure_date.isoformat(),
                            status="skipped_unsupported" if reason else "pending",
                            last_error_code="unsupported_query" if reason else None,
                            last_error_detail=reason,
                            finished_at=now if reason else None,
                        )
                    )
            s.flush()
            self.finalize(s, job, now)
            return job

    def get_job(self, job_id):
        with Session(self.engine) as s:
            job = s.get(SearchJob, job_id)
            if job is None:
                raise KeyError(job_id)
            items = s.scalars(
                select(WorkItem)
                .where(WorkItem.job_id == job_id)
                .order_by(
                    WorkItem.provider_id,
                    WorkItem.origin,
                    WorkItem.destination,
                    WorkItem.departure_date,
                )
            ).all()
            return job, items

    @staticmethod
    def finalize(s, job, now):
        s.flush()
        items = s.scalars(select(WorkItem).where(WorkItem.job_id == job.id)).all()
        job.updated_at = now
        if any(i.status in ACTIVE for i in items):
            return
        counts = Counter(i.status for i in items)
        successes = sum(counts[k] for k in SUCCESS)
        if job.cancel_requested:
            job.status = "cancelled"
        elif successes == len(items) and items:
            job.status = "completed"
        elif successes:
            job.status = "partial"
        else:
            job.status = "failed"
        job.phase = "done"
        job.completed_at = now

    def cancel(self, job_id):
        from cheapwings.storage.models import WorkAttempt

        with write_session(self.engine) as s:
            job = s.get(SearchJob, job_id)
            if job is None:
                raise KeyError(job_id)
            if job.status not in JOB_ACTIVE:
                return
            job.cancel_requested = True
            for item in s.scalars(
                select(WorkItem).where(WorkItem.job_id == job_id, WorkItem.status.in_(ACTIVE))
            ):
                if item.status == "running":
                    attempt = s.scalar(
                        select(WorkAttempt).where(
                            WorkAttempt.work_item_id == item.id,
                            WorkAttempt.attempt == item.attempts,
                        )
                    )
                    attempt.outcome = "cancelled"
                    attempt.finished_at = now_ms()
                item.status = "cancelled"
                item.lease_token = None
                item.leased_until = None
                item.finished_at = now_ms()
            self.finalize(s, job, now_ms())

    def sweep(self, *, max_attempts=3, now=None):
        """Run on startup AND each tick: never steals an unexpired lease."""
        from cheapwings.storage.models import WorkAttempt

        now = now if now is not None else now_ms()
        with write_session(self.engine) as s:
            for job in s.scalars(select(SearchJob).where(SearchJob.status.in_(JOB_ACTIVE))):
                for item in s.scalars(
                    select(WorkItem).where(WorkItem.job_id == job.id, WorkItem.status.in_(ACTIVE))
                ):
                    expired = item.status == "running" and item.leased_until <= now
                    budget = job.deadline_at <= now
                    if not expired and not budget:
                        continue
                    if item.status == "running":
                        attempt = s.scalar(
                            select(WorkAttempt).where(
                                WorkAttempt.work_item_id == item.id,
                                WorkAttempt.attempt == item.attempts,
                            )
                        )
                        attempt.outcome = "budget_exhausted" if budget else "lease_expired"
                        attempt.finished_at = now
                        attempt.error_code = "network_timeout"
                    terminal = budget or item.attempts >= max_attempts
                    item.status = "failed_terminal" if terminal else "pending"
                    item.last_error_code = "network_timeout"
                    item.last_error_detail = (
                        "job budget exhausted" if budget else "worker lease expired"
                    )
                    item.lease_token = None
                    item.leased_until = None
                    if terminal:
                        item.finished_at = now
                self.finalize(s, job, now)

    def claim(self, registration, *, lease_seconds=40, now=None):
        from cheapwings.storage.models import ProviderState, WorkAttempt

        now = now if now is not None else now_ms()
        provider_id = registration.provider.provider_id
        if registration.unavailable_reason:
            return None
        with write_session(self.engine) as s:
            state = s.get(ProviderState, provider_id)
            if state is None:
                state = ProviderState(provider_id=provider_id, next_request_at=0)
                s.add(state)
            if state.next_request_at > now:
                return None
            running = s.scalars(
                select(WorkItem).where(
                    WorkItem.provider_id == provider_id, WorkItem.status == "running"
                )
            ).all()
            if len(running) >= registration.concurrency:
                return None
            item = s.scalar(
                select(WorkItem)
                .join(SearchJob)
                .where(
                    WorkItem.provider_id == provider_id,
                    WorkItem.status.in_(("pending", "retry_wait")),
                    WorkItem.next_attempt_at <= now,
                    SearchJob.status.in_(JOB_ACTIVE),
                    SearchJob.cancel_requested.is_(False),
                    SearchJob.deadline_at > now,
                )
                .order_by(SearchJob.created_at, WorkItem.departure_date, WorkItem.id)
                .limit(1)
            )
            if item is None:
                return None
            item.status = "running"
            item.attempts += 1
            item.started_at = now
            item.lease_token = str(uuid4())
            item.leased_until = now + int(lease_seconds * 1000)
            s.add(WorkAttempt(work_item_id=item.id, attempt=item.attempts, started_at=now))
            state.next_request_at = now + int(registration.minimum_interval_seconds * 1000)
            job = s.get(SearchJob, item.job_id)
            job.status = "running"
            job.updated_at = now
            return item, SearchQuery.model_validate(job.query_json)

    def finish(
        self,
        item_id,
        token,
        result=None,
        *,
        error_code=None,
        retry_after_seconds=0,
        max_attempts=3,
        now=None,
    ):
        from cheapwings.storage.models import ProviderState, WorkAttempt

        now = now if now is not None else now_ms()
        with write_session(self.engine) as s:
            item = s.get(WorkItem, item_id)
            job = s.get(SearchJob, item.job_id)
            if (
                item.status != "running"
                or item.lease_token != token
                or item.leased_until <= now
                or job.cancel_requested
            ):
                return False  # cancelled, expired or superseded: fence late completions
            attempt = s.scalar(
                select(WorkAttempt).where(
                    WorkAttempt.work_item_id == item.id, WorkAttempt.attempt == item.attempts
                )
            )
            if job.deadline_at <= now:
                error_code = "network_timeout"
                max_attempts = item.attempts
            if error_code:
                retryable = error_code in (
                    "network_timeout",
                    "http_rate_limited",
                    "provider_unavailable",
                )
                delay_ms = max(
                    int(retry_after_seconds * 1000), min(60_000, 1000 * 2 ** (item.attempts - 1))
                )
                item.status = (
                    "retry_wait"
                    if retryable and item.attempts < max_attempts
                    else "failed_terminal"
                )
                item.last_error_code = error_code
                item.last_error_detail = error_code  # never log/store raw exception or tokens
                item.next_attempt_at = now + delay_ms
                if error_code == "http_rate_limited":
                    state = s.get(ProviderState, item.provider_id)
                    state.next_request_at = max(state.next_request_at, now + delay_ms)
                attempt.error_code = error_code
            else:
                self._store_results(s, job, item, result, now)
                item.status = result.status.value
                item.provider_complete = result.provider_complete
                item.result_count = sum(len(o) for o in result.offers_by_itinerary_index)
                item.last_error_code = None
                item.last_error_detail = None
            attempt.outcome = item.status
            attempt.finished_at = now
            item.lease_token = None
            item.leased_until = None
            if item.status != "retry_wait":
                item.finished_at = now
            self.finalize(s, job, now)
            return True

    @staticmethod
    def _store_results(s, job, item, result, now):
        from dataclasses import replace

        from pydantic import TypeAdapter

        from cheapwings.domain.offer import ComparisonStatus, Offer, ThreeValued
        from cheapwings.domain.segments import FlightSegment
        from cheapwings.engine.matching import build_itinerary
        from cheapwings.storage.models import FareQuote, ItineraryRow, QuoteRevision, SegmentRow

        for segments, offers in zip(result.itineraries, result.offers_by_itinerary_index):
            itin = build_itinerary(segments, str(uuid4()))
            row = (
                s.scalar(
                    select(ItineraryRow).where(
                        ItineraryRow.job_id == job.id, ItineraryRow.fingerprint == itin.fingerprint
                    )
                )
                if itin.fingerprint
                else None
            )
            if row is None:
                row = ItineraryRow(
                    id=itin.itinerary_id,
                    job_id=job.id,
                    fingerprint=itin.fingerprint,
                    identity_confidence=itin.identity_confidence.value,
                )
                s.add(row)
                s.flush()
                for seg in segments:
                    s.add(
                        SegmentRow(
                            itinerary_id=row.id,
                            ordinal=seg.ordinal,
                            canonical_json=TypeAdapter(FlightSegment).dump_python(seg, mode="json"),
                        )
                    )
            for offer in offers:
                exists = s.scalar(
                    select(FareQuote).where(
                        FareQuote.job_id == job.id,
                        FareQuote.provider_id == item.provider_id,
                        FareQuote.source_quote_id == offer.quote_id,
                    )
                )
                if exists:
                    continue
                query = job.query_json
                comparison = offer.comparison_status
                if query["checked_bags_required"] and offer.checked_bag != ThreeValued.YES:
                    comparison = ComparisonStatus.MISSING_REQUIRED_BAGGAGE
                if (query["max_stops"] != "any" and itin.stops > int(query["max_stops"])) or (
                    not query["include_basic_economy"] and offer.basic_economy
                ):
                    comparison = ComparisonStatus.INELIGIBLE
                public_offer = replace(
                    offer,
                    itinerary_id=row.id,
                    comparison_status=comparison,
                    provider_quote_handle=None,
                )
                data = TypeAdapter(Offer).dump_python(public_offer, mode="json")
                data.pop("provider_quote_handle")
                quote = FareQuote(
                    job_id=job.id,
                    itinerary_id=row.id,
                    provider_id=item.provider_id,
                    source_quote_id=offer.quote_id,
                    raw_amount_decimal_text=str(offer.amount_original.amount),
                    raw_currency=offer.amount_original.currency,
                    comparable_amount_decimal_text=(
                        str(offer.comparable_amount.amount) if offer.comparable_amount else None
                    ),
                    comparable_currency=(
                        offer.comparable_amount.currency if offer.comparable_amount else None
                    ),
                    canonical_json=data,
                    provider_quote_handle_server_side=offer.provider_quote_handle,
                )
                s.add(quote)
                s.flush()
                s.add(
                    QuoteRevision(
                        quote_id=quote.id,
                        revision_time=now,
                        amount_decimal_text=quote.raw_amount_decimal_text,
                        currency=quote.raw_currency,
                        reason="initial_search",
                    )
                )

    def reconcile_registry(self, registry):
        """Configuration changes leave explicit skipped entries rather than stuck jobs."""
        from cheapwings.storage.models import WorkAttempt

        reasons = {r.provider.provider_id: r.unavailable_reason for r in registry}
        with write_session(self.engine) as s:
            jobs = set()
            for item in s.scalars(select(WorkItem).where(WorkItem.status.in_(ACTIVE))):
                reason = reasons.get(item.provider_id, "provider removed from worker registry")
                if not reason:
                    continue
                if item.status == "running":
                    attempt = s.scalar(
                        select(WorkAttempt).where(
                            WorkAttempt.work_item_id == item.id,
                            WorkAttempt.attempt == item.attempts,
                        )
                    )
                    attempt.outcome = "skipped_unsupported"
                    attempt.finished_at = now_ms()
                    attempt.error_code = "unsupported_query"
                item.status = "skipped_unsupported"
                item.last_error_code = "unsupported_query"
                item.last_error_detail = reason
                item.finished_at = now_ms()
                item.lease_token = None
                item.leased_until = None
                jobs.add(item.job_id)
            for job_id in jobs:
                self.finalize(s, s.get(SearchJob, job_id), now_ms())
