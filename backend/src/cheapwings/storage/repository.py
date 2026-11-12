"""Short SQLite transactions. No provider I/O may occur inside a transaction."""

from collections import Counter
from time import time_ns
from uuid import uuid4

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from cheapwings.domain.query import SearchQuery
from cheapwings.engine.expansion import expand_routes_and_dates
from cheapwings.storage.cache import CacheRepository
from cheapwings.storage.db import write_session
from cheapwings.storage.models import SearchJob, WorkItem
from cheapwings.storage.verification import VerificationRepository
from cheapwings.typeadapters import adapter

ACTIVE = ("pending", "retry_wait", "running")
SUCCESS = ("succeeded_results", "succeeded_empty")
JOB_ACTIVE = ("queued", "running")


def now_ms():
    return time_ns() // 1_000_000


class CapacityExceeded(Exception):
    pass


class Repository(CacheRepository, VerificationRepository):
    def __init__(
        self,
        engine,
        *,
        global_capacity=9,
        cache_enabled=False,
        cache_ttl_seconds=1200,
        cache_max_entries=2000,
        cache_max_bytes=20_000_000,
    ):
        self.engine = engine
        if global_capacity < 1:
            raise ValueError("Global capacity must be positive")
        self.global_capacity = global_capacity
        self.cache_enabled = cache_enabled
        self.cache_ttl_seconds = cache_ttl_seconds
        self.cache_max_entries = cache_max_entries
        self.cache_max_bytes = cache_max_bytes

    def create_job(
        self,
        query: SearchQuery,
        registry,
        *,
        max_active=2,
        max_hourly=20,
        budget_seconds=1800,
        reprice_budget=0,
        retention_seconds=None,
        cache_mode="prefer_cache",
        max_requests=100,
        max_active_requests=20,
    ):
        now = now_ms()
        with write_session(self.engine) as s:
            jobs = s.scalars(select(SearchJob)).all()
            if (
                sum(j.created_at > now - 3_600_000 for j in jobs) >= max_requests
                or sum(j.status in JOB_ACTIVE for j in jobs) >= max_active_requests
            ):
                raise CapacityExceeded("Search request limit exceeded; wait for capacity")
            job = SearchJob(
                id=str(uuid4()),
                # New arrivals join the current round instead of repeatedly
                # jumping ahead of jobs that have already received service.
                dispatch_sequence=s.scalar(select(func.max(SearchJob.dispatch_sequence))) or 0,
                provider_ids=[r.provider.provider_id for r in registry if not r.unavailable_reason],
                cache_mode=cache_mode,
                query_json={
                    **query.model_dump(mode="json"),
                    "max_combinations": query.max_combinations,
                },
                created_at=now,
                updated_at=now,
                deadline_at=now + budget_seconds * 1000,
                data_expires_at=now + retention_seconds * 1000 if retention_seconds else None,
                reprice_budget=reprice_budget,
                reprice_providers=[
                    r.provider.provider_id
                    for r in registry
                    if not r.unavailable_reason and r.provider.capabilities.exact_reprice
                ],
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
            reserved = False
            for registration in registry:
                created = self.prepare_cached_work(s, job, registration, now)
                pending = s.scalars(
                    select(WorkItem).where(
                        WorkItem.job_id == job.id,
                        WorkItem.provider_id == registration.provider.provider_id,
                        WorkItem.status.in_(ACTIVE),
                        WorkItem.operation_id.is_(None),
                    )
                ).all()
                reserved = reserved or created or bool(pending)
            job.upstream_work_reserved = reserved
            if reserved and (
                sum(j.status in JOB_ACTIVE and j.upstream_work_reserved for j in jobs) >= max_active
                or sum(j.created_at > now - 3_600_000 and j.upstream_work_reserved for j in jobs)
                >= max_hourly
            ):
                raise CapacityExceeded("Search creation budget exceeded; wait for capacity")
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
        job.updated_at = now
        # Called on every finish: one indexed existence check while work remains,
        # instead of loading every item of the job (quadratic in job size).
        if s.scalar(
            select(WorkItem.id)
            .where(WorkItem.job_id == job.id, WorkItem.status.in_(ACTIVE))
            .limit(1)
        ):
            return
        if job.deadline_at <= now:
            job.verification_planned = True
        if (
            not job.cancel_requested
            and job.reprice_budget
            and job.reprice_providers
            and not job.verification_planned
        ):
            job.status = "running"
            job.phase = "verifying"
            return
        counts = Counter(
            dict(
                s.execute(
                    select(WorkItem.status, func.count())
                    .where(WorkItem.job_id == job.id)
                    .group_by(WorkItem.status)
                ).all()
            )
        )
        total = sum(counts.values())
        successes = sum(counts[k] for k in SUCCESS)
        if job.cancel_requested:
            job.status = "cancelled"
        elif successes == total and total:
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
                if item.status == "running" and item.operation_id is None:
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
        self.sweep_operations(now=now, max_attempts=max_attempts)
        with write_session(self.engine) as s:
            for job in s.scalars(select(SearchJob).where(SearchJob.status.in_(JOB_ACTIVE))):
                for item in s.scalars(
                    select(WorkItem).where(WorkItem.job_id == job.id, WorkItem.status.in_(ACTIVE))
                ):
                    expired = (
                        item.operation_id is None
                        and item.status == "running"
                        and item.leased_until <= now
                    )
                    budget = job.deadline_at <= now
                    if not expired and not budget:
                        continue
                    if item.status == "running" and item.operation_id is None:
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

    def claim(
        self, registration, *, lease_seconds=40, now=None, exclude_ids=(), exclude_cache_keys=()
    ):
        from cheapwings.storage.models import ProviderOperation, ProviderState, WorkAttempt

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
            # Shared subscribers are not extra execution slots. These checks and
            # the selected claim share one BEGIN IMMEDIATE transaction.
            direct = s.scalars(
                select(WorkItem).where(
                    WorkItem.status == "running", WorkItem.operation_id.is_(None)
                )
            ).all()
            operations = s.scalars(
                select(ProviderOperation).where(ProviderOperation.status == "running")
            ).all()
            if len(direct) + len(operations) >= self.global_capacity:
                return None
            item = s.scalar(
                select(WorkItem)
                .join(SearchJob)
                .outerjoin(ProviderOperation, WorkItem.operation_id == ProviderOperation.id)
                .where(
                    WorkItem.provider_id == provider_id,
                    WorkItem.id.not_in(exclude_ids),
                    or_(WorkItem.operation_id.is_(None), WorkItem.operation_id.not_in(exclude_ids)),
                    or_(
                        WorkItem.operation_id.is_(None),
                        ProviderOperation.cache_key.not_in(exclude_cache_keys),
                    ),
                    WorkItem.status.in_(("pending", "retry_wait")),
                    SearchJob.status.in_(JOB_ACTIVE),
                    SearchJob.cancel_requested.is_(False),
                    SearchJob.deadline_at > now,
                    or_(
                        and_(WorkItem.operation_id.is_(None), WorkItem.next_attempt_at <= now),
                        and_(
                            ProviderOperation.status.in_(("pending", "retry_wait")),
                            ProviderOperation.next_attempt_at <= now,
                            ProviderOperation.deadline_at > now,
                        ),
                    ),
                )
                .order_by(
                    SearchJob.dispatch_sequence,
                    SearchJob.created_at,
                    SearchJob.id,
                    WorkItem.departure_date,
                    WorkItem.id,
                )
                .limit(1)
            )
            if item is None:
                return None
            sequence = (s.scalar(select(func.max(SearchJob.dispatch_sequence))) or 0) + 1
            if item.operation_id:
                claimed = self.claim_operation(
                    s, registration, now, lease_seconds, operation_id=item.operation_id
                )
                if claimed is None:
                    return None
                # Every active subscriber benefits from this dispatch.
                for subscriber in s.scalars(
                    select(WorkItem).where(WorkItem.operation_id == item.operation_id)
                ):
                    s.get(SearchJob, subscriber.job_id).dispatch_sequence = sequence
                state.next_request_at = now + int(registration.minimum_interval_seconds * 1000)
                claimed[0].dispatch_reserved_until = state.next_request_at
                return claimed
            s.get(SearchJob, item.job_id).dispatch_sequence = sequence
            item.status = "running"
            item.attempts += 1
            item.started_at = now
            if item.data_expires_at is None and registration.retention_seconds:
                item.data_expires_at = now + registration.retention_seconds * 1000
            item.lease_token = str(uuid4())
            item.leased_until = now + int(lease_seconds * 1000)
            s.add(WorkAttempt(work_item_id=item.id, attempt=item.attempts, started_at=now))
            state.next_request_at = now + int(registration.minimum_interval_seconds * 1000)
            job = s.get(SearchJob, item.job_id)
            job.status = "running"
            job.updated_at = now
            item.dispatch_reserved_until = state.next_request_at
            return item, SearchQuery.model_validate(job.query_json)

    @staticmethod
    def provider_feedback(s, provider_id, error_code, retry_after_seconds, now):
        """Provider-wide feedback survives result fencing and job cancellation."""
        if error_code == "http_rate_limited":
            from cheapwings.storage.models import ProviderState

            state = s.get(ProviderState, provider_id)
            if state is None:
                state = ProviderState(provider_id=provider_id, next_request_at=0)
                s.add(state)
            state.next_request_at = max(
                state.next_request_at, now + int(max(1, retry_after_seconds or 60) * 1000)
            )

    def pool_snapshot(self):
        """Running slots per provider (a shared operation counts once) and start deadlines."""
        from cheapwings.storage.models import ProviderOperation, ProviderState

        with Session(self.engine) as s:
            running = Counter(
                s.scalars(
                    select(WorkItem.provider_id).where(
                        WorkItem.status == "running", WorkItem.operation_id.is_(None)
                    )
                )
            )
            running.update(
                s.scalars(
                    select(ProviderOperation.provider_id).where(
                        ProviderOperation.status == "running"
                    )
                )
            )
            deadlines = dict(
                s.execute(select(ProviderState.provider_id, ProviderState.next_request_at)).all()
            )
        return running, deadlines

    def record_provider_feedback(self, provider_id, error_code, retry_after_seconds=0):
        with write_session(self.engine) as s:
            self.provider_feedback(s, provider_id, error_code, retry_after_seconds, now_ms())

    def mark_started(self, registration, claimed):
        """Re-check fencing/cooldown and persist actual adapter dispatch time."""
        from cheapwings.storage.models import (
            OperationAttempt,
            ProviderOperation,
            ProviderState,
            WorkAttempt,
        )

        now = now_ms()
        with write_session(self.engine) as s:
            shared = claimed.id.startswith("fetch-")
            item = s.get(ProviderOperation if shared else WorkItem, claimed.id)
            if (
                not item
                or item.status != "running"
                or item.lease_token != claimed.lease_token
                or item.leased_until <= now
            ):
                return False
            if shared:
                subscriber = s.scalar(
                    select(WorkItem.id)
                    .join(SearchJob)
                    .where(
                        WorkItem.operation_id == item.id,
                        WorkItem.status.in_(ACTIVE),
                        SearchJob.status.in_(JOB_ACTIVE),
                        SearchJob.cancel_requested.is_(False),
                        SearchJob.deadline_at > now,
                    )
                    .limit(1)
                )
                if subscriber is None:
                    attempt = s.scalar(
                        select(OperationAttempt).where(
                            OperationAttempt.operation_id == item.id,
                            OperationAttempt.attempt == item.attempts,
                        )
                    )
                    attempt.outcome, attempt.finished_at = "cancelled", now
                    item.status = "cancelled"
                    item.lease_token = item.leased_until = None
                    return False
                if item.deadline_at <= now or item.hard_expires_at <= now:
                    return False
            else:
                job = s.get(SearchJob, item.job_id)
                if job.cancel_requested or job.deadline_at <= now:
                    return False
            state = s.get(ProviderState, registration.provider.provider_id)
            if state.next_request_at > max(
                now, getattr(claimed, "dispatch_reserved_until", state.next_request_at)
            ):
                # Another in-flight call supplied a cooldown after this claim.
                # Defer the unsent claim without consuming a retry attempt.
                attempt_model = OperationAttempt if shared else WorkAttempt
                key = attempt_model.operation_id if shared else attempt_model.work_item_id
                attempt = s.scalar(
                    select(attempt_model).where(
                        key == item.id, attempt_model.attempt == item.attempts
                    )
                )
                s.delete(attempt)
                item.attempts -= 1
                item.status = "retry_wait"
                item.next_attempt_at = state.next_request_at
                item.lease_token = item.leased_until = None
                if shared:
                    self.fail_subscribers(s, item, "http_rate_limited", now, terminal=False)
                return False
            state.next_request_at = max(
                state.next_request_at, now + int(registration.minimum_interval_seconds * 1000)
            )
            return True

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
        if item_id.startswith("fetch-"):
            return self.finish_operation(
                item_id,
                token,
                result,
                error_code=error_code,
                retry_after_seconds=retry_after_seconds,
                max_attempts=max_attempts,
                now=now,
            )
        with write_session(self.engine) as s:
            item = s.get(WorkItem, item_id)
            if item is None:
                return False
            self.provider_feedback(s, item.provider_id, error_code, retry_after_seconds, now)
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
                if item.work_type == "reprice" and item.status == "failed_terminal":
                    job.verification_planned = False
            else:
                if item.work_type == "reprice":
                    self._store_reprice(s, job, item, result, now)
                    item.status = "succeeded_results" if result.available else "succeeded_empty"
                else:
                    item.observation_retrieved_at = int(result.retrieved_at.timestamp() * 1000)
                    self._store_results(s, job, item, result, now)
                    item.status = result.status.value
                item.provider_complete = getattr(result, "provider_complete", None)
                item.result_count = (
                    len(result.offers)
                    if item.work_type == "reprice"
                    else sum(len(o) for o in result.offers_by_itinerary_index)
                )
                item.unpriced_candidate_count = getattr(result, "unpriced_candidate_count", 0)
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

        from cheapwings.domain.itinerary import (
            AirportTransfer,
            IdentityConfidence,
            Itinerary,
            ItinerarySummary,
        )
        from cheapwings.domain.offer import ComparisonStatus, Offer, ThreeValued
        from cheapwings.domain.segments import FlightSegment
        from cheapwings.engine.matching import build_itinerary
        from cheapwings.storage.models import (
            FareQuote,
            FXRow,
            ItineraryRow,
            QuoteRevision,
            SegmentRow,
        )

        for index, (segments, offers) in enumerate(
            zip(result.itineraries, result.offers_by_itinerary_index)
        ):
            summary = result.itinerary_summaries[index] if result.itinerary_summaries else None
            transfers = (
                result.airport_transfers_by_itinerary_index[index]
                if result.airport_transfers_by_itinerary_index
                else ()
            )
            itin = (
                Itinerary(
                    str(uuid4()), (), IdentityConfidence.INSUFFICIENT_IDENTITY, summary=summary
                )
                if summary
                else build_itinerary(segments, str(uuid4()), transfers)
            )
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
                    airport_transfers_json=adapter(tuple[AirportTransfer, ...]).dump_python(
                        transfers, mode="json"
                    ),
                    summary_json=adapter(ItinerarySummary).dump_python(summary, mode="json")
                    if summary
                    else None,
                )
                s.add(row)
                s.flush()
                for seg in segments:
                    s.add(
                        SegmentRow(
                            itinerary_id=row.id,
                            ordinal=seg.ordinal,
                            canonical_json=adapter(FlightSegment).dump_python(seg, mode="json"),
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
                if transfers and comparison == ComparisonStatus.ELIGIBLE_TOTAL_KNOWN:
                    comparison = ComparisonStatus.EXTRA_COST_UNKNOWN
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
                data = adapter(Offer).dump_python(public_offer, mode="json")
                data.pop("provider_quote_handle")
                fx_row = None
                if offer.evidence and offer.evidence.fx_snapshot:
                    fx = offer.evidence.fx_snapshot
                    from datetime import datetime

                    fx_row = FXRow(
                        base=fx.base_currency,
                        quote=fx.quote_currency,
                        rate_decimal_text=str(fx.rate),
                        source=fx.source,
                        observed_at=int(datetime.fromisoformat(fx.retrieved_at).timestamp() * 1000),
                    )
                    s.add(fx_row)
                    s.flush()
                quote = FareQuote(
                    work_item_id=item.id,
                    fx_snapshot_id=fx_row.id if fx_row else None,
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
                        canonical_json=data,
                    )
                )

    def reconcile_registry(self, registry):
        """Configuration changes leave explicit skipped entries rather than stuck jobs."""
        from cheapwings.storage.models import WorkAttempt

        reasons = {r.provider.provider_id: r.unavailable_reason for r in registry}
        with write_session(self.engine) as s:
            self.reconcile_operations(s, registry, now_ms())
            jobs = set()
            for item in s.scalars(select(WorkItem).where(WorkItem.status.in_(ACTIVE))):
                reason = reasons.get(item.provider_id, "provider removed from worker registry")
                if not reason:
                    continue
                if item.status == "running" and item.operation_id is None:
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
