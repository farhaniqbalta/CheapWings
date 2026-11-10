"""Provider-neutral immutable observations and fenced, job-independent fetches."""

import json
from dataclasses import replace
from importlib.metadata import PackageNotFoundError, version
from uuid import uuid4

from pydantic import TypeAdapter
from sqlalchemy import delete, select

from cheapwings.domain.offer import PriceStatus
from cheapwings.domain.query import SearchQuery
from cheapwings.providers.base import ProviderSearchResult
from cheapwings.storage.db import write_session
from cheapwings.storage.models import (
    OperationAttempt,
    ProviderOperation,
    ProviderResultCache,
    ProviderState,
    SearchJob,
    WorkItem,
)

RESULT = TypeAdapter(ProviderSearchResult)
ACTIVE = ("pending", "running", "retry_wait")


def cache_key(job, item, registration):
    provider = registration.provider
    packages = {}
    for name in getattr(provider, "cache_dependencies", ()):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = "unavailable"
    query = job.query_json
    # Full canonical key is retained, not a collision-prone truncated digest.
    return json.dumps(
        {
            "version": 2,
            "provider": item.provider_id,
            "adapter": f"{type(provider).__module__}.{type(provider).__qualname__}",
            "adapter_version": getattr(provider, "cache_version", "1"),
            "dependencies": packages,
            "source_options": getattr(provider, "cache_options", {}),
            "limit": getattr(provider, "limit", None),
            "policy": registration.usage_policy_reviewed_on,
            "retention": registration.retention_seconds,
            "scope": "personal",
            "origin": item.origin,
            "destination": item.destination,
            "date": item.departure_date,
            **{
                name: query[name]
                for name in (
                    "trip_type",
                    "adults",
                    "cabin",
                    "include_basic_economy",
                    "include_hidden_city",
                    "display_currency",
                    "point_of_sale_country",
                    "max_stops",
                    "checked_bags_required",
                )
            },
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def without_handles(result):
    return replace(
        result,
        offers_by_itinerary_index=tuple(
            tuple(
                replace(
                    o,
                    provider_quote_handle=None,
                    repriced_at=None,
                    price_status=PriceStatus.RECENT_SEARCH
                    if o.price_status == PriceStatus.REPRICED_EXACT
                    else o.price_status,
                )
                for o in offers
            )
            for offers in result.offers_by_itinerary_index
        ),
    )


class CacheRepository:
    def prepare_cached_work(self, s, job, registration, now):
        """Inside admission transaction: a hit cannot race expiry or live quota reservation."""
        if not self.cache_enabled or registration.unavailable_reason or not registration.can_cache:
            return False
        reserved = False
        for item in s.scalars(
            select(WorkItem).where(
                WorkItem.job_id == job.id,
                WorkItem.provider_id == registration.provider.provider_id,
                WorkItem.work_type == "detailed",
                WorkItem.status == "pending",
            )
        ):
            key = cache_key(job, item, registration)
            hit = (
                None
                if job.cache_mode == "refresh"
                else s.scalar(
                    select(ProviderResultCache)
                    .where(
                        ProviderResultCache.cache_key == key,
                        ProviderResultCache.fresh_until > now,
                        ProviderResultCache.hard_expires_at > now,
                    )
                    .order_by(ProviderResultCache.cached_at.desc())
                    .limit(1)
                )
            )
            if hit:
                result = RESULT.validate_json(hit.payload_json)
                self.deliver_observation(
                    s,
                    job,
                    item,
                    result,
                    now,
                    hit.hard_expires_at,
                    origin="cache",
                    fresh_until=hit.fresh_until,
                )
                continue
            # Refresh requests cannot join an observation that started before their request.
            operation = s.scalar(
                select(ProviderOperation)
                .where(
                    ProviderOperation.cache_key == key,
                    ProviderOperation.status.in_(ACTIVE),
                    ProviderOperation.deadline_at > now,
                    ProviderOperation.hard_expires_at > now,
                    *(
                        [ProviderOperation.created_at >= job.created_at]
                        if job.cache_mode == "refresh"
                        else []
                    ),
                )
                .order_by(ProviderOperation.created_at)
                .limit(1)
            )
            if operation is None:
                hard = min(
                    job.data_expires_at or now + 3_600_000,
                    now + (registration.retention_seconds or 3600) * 1000,
                )
                operation = ProviderOperation(
                    id="fetch-" + str(uuid4()),
                    cache_key=key,
                    provider_id=item.provider_id,
                    query_json=job.query_json,
                    origin=item.origin,
                    destination=item.destination,
                    departure_date=item.departure_date,
                    status="pending",
                    created_at=now,
                    deadline_at=min(job.deadline_at, hard),
                    hard_expires_at=hard,
                    primary_work_item_id=item.id,
                    cache_ttl_seconds=min(self.cache_ttl_seconds, registration.cache_ttl_seconds),
                )
                s.add(operation)
                s.flush()
                reserved = True
            else:
                item.result_origin = "shared_inflight"
            item.operation_id = operation.id
            item.status = "running" if operation.status == "running" else "pending"
            item.started_at = now if operation.status == "running" else None
        return reserved

    def deliver_observation(
        self, s, job, item, result, now, hard, *, origin=None, fresh_until=None
    ):
        if (
            job.cancel_requested
            or job.status not in ("queued", "running")
            or job.deadline_at <= now
            or hard <= now
        ):
            return
        if origin:
            item.result_origin = origin
        if item.result_origin in ("cache", "shared_inflight"):
            result = without_handles(result)
            item.reused_at = now
        item.data_expires_at = min(item.data_expires_at or hard, hard)
        if job.data_expires_at is not None:  # preserve legacy explicit retention bounds
            job.data_expires_at = min(job.data_expires_at, hard)
        self._store_results(s, job, item, result, now)
        item.observation_retrieved_at = int(result.retrieved_at.timestamp() * 1000)
        item.cache_fresh_until = fresh_until
        item.status = result.status.value
        item.provider_complete = result.provider_complete
        item.result_count = sum(len(o) for o in result.offers_by_itinerary_index)
        item.unpriced_candidate_count = result.unpriced_candidate_count
        item.finished_at = now
        item.last_error_code = item.last_error_detail = None
        self.finalize(s, job, now)

    def claim_operation(self, s, registration, now, lease_seconds):
        provider_id = registration.provider.provider_id
        operation = s.scalar(
            select(ProviderOperation)
            .where(
                ProviderOperation.provider_id == provider_id,
                ProviderOperation.status.in_(("pending", "retry_wait")),
                ProviderOperation.next_attempt_at <= now,
                ProviderOperation.deadline_at > now,
            )
            .order_by(
                ProviderOperation.created_at, ProviderOperation.departure_date, ProviderOperation.id
            )
            .limit(1)
        )
        if operation is None:
            return None
        # Re-check current parser, policy, source options and feature state before dispatch.
        subscribers = s.scalars(
            select(WorkItem)
            .join(SearchJob)
            .where(
                WorkItem.operation_id == operation.id,
                WorkItem.status.in_(ACTIVE),
                SearchJob.status.in_(("queued", "running")),
                SearchJob.cancel_requested.is_(False),
                SearchJob.deadline_at > now,
            )
        ).all()
        if not subscribers:
            operation.status = "cancelled"
            return None
        for item in subscribers:
            job = s.get(SearchJob, item.job_id)
            if (
                not self.cache_enabled
                or not registration.can_cache
                or cache_key(job, item, registration) != operation.cache_key
            ):
                operation.status = "failed_terminal"
                self.fail_subscribers(s, operation, "unsupported_query", now)
                return None
        operation.status = "running"
        operation.attempts += 1
        operation.lease_token = str(uuid4())
        operation.leased_until = now + int(lease_seconds * 1000)
        s.add(
            OperationAttempt(operation_id=operation.id, attempt=operation.attempts, started_at=now)
        )
        for item in subscribers:
            item.status = "running"
            item.started_at = item.started_at or now
            job = s.get(SearchJob, item.job_id)
            job.status = "running"
            job.updated_at = now
        return operation, SearchQuery.model_validate(operation.query_json)

    def fail_subscribers(self, s, operation, error, now, terminal=True):
        for item in s.scalars(
            select(WorkItem).where(
                WorkItem.operation_id == operation.id,
                WorkItem.status.in_(ACTIVE),
            )
        ):
            item.status = "failed_terminal" if terminal else "retry_wait"
            item.last_error_code = item.last_error_detail = error
            if terminal:
                item.finished_at = now
            self.finalize(s, s.get(SearchJob, item.job_id), now)

    def finish_operation(
        self, item_id, token, result, *, error_code=None, retry_after_seconds=0, max_attempts=3, now
    ):
        with write_session(self.engine) as s:
            operation = s.get(ProviderOperation, item_id)
            if (
                not operation
                or operation.status != "running"
                or operation.lease_token != token
                or operation.leased_until <= now
            ):
                return False
            attempt = s.scalar(
                select(OperationAttempt).where(
                    OperationAttempt.operation_id == operation.id,
                    OperationAttempt.attempt == operation.attempts,
                )
            )
            if operation.deadline_at <= now or operation.hard_expires_at <= now:
                error_code, max_attempts = "network_timeout", operation.attempts
            if error_code:
                retry = (
                    error_code in ("network_timeout", "provider_unavailable", "http_rate_limited")
                    and operation.attempts < max_attempts
                )
                delay = max(
                    int(retry_after_seconds * 1000),
                    min(60_000, 1000 * 2 ** (operation.attempts - 1)),
                )
                operation.status = "retry_wait" if retry else "failed_terminal"
                operation.next_attempt_at = now + delay
                operation.error_code = error_code
                if error_code == "http_rate_limited":
                    state = s.get(ProviderState, operation.provider_id)
                    state.next_request_at = max(state.next_request_at, now + delay)
                self.fail_subscribers(s, operation, error_code, now, terminal=not retry)
            else:
                eligible = result.provider_complete is True and result.unpriced_candidate_count == 0
                retrieved = int(result.retrieved_at.timestamp() * 1000)
                observations = [retrieved] + [
                    int(o.evidence.source_checked_at.timestamp() * 1000)
                    for offers in result.offers_by_itinerary_index
                    for o in offers
                    if o.evidence and o.evidence.source_checked_at
                ]
                fresh = min(
                    min(observations) + operation.cache_ttl_seconds * 1000,
                    operation.hard_expires_at,
                )
                payload = RESULT.dump_json(without_handles(result)).decode()
                subscribers_exist = (
                    s.scalar(
                        select(WorkItem.id)
                        .join(SearchJob)
                        .where(
                            WorkItem.operation_id == operation.id,
                            WorkItem.status.in_(ACTIVE),
                            SearchJob.status.in_(("queued", "running")),
                            SearchJob.cancel_requested.is_(False),
                            SearchJob.deadline_at > now,
                        )
                        .limit(1)
                    )
                    is not None
                )
                if (
                    self.cache_enabled
                    and subscribers_exist
                    and eligible
                    and fresh > now
                    and len(payload.encode()) <= self.cache_max_bytes
                ):
                    # Replacement must never redate the underlying observation.
                    s.add(
                        ProviderResultCache(
                            id=str(uuid4()),
                            cache_key=operation.cache_key,
                            provider_id=operation.provider_id,
                            payload_json=payload,
                            retrieved_at=retrieved,
                            cached_at=now,
                            fresh_until=fresh,
                            hard_expires_at=operation.hard_expires_at,
                            byte_size=len(payload.encode()),
                        )
                    )
                for item in s.scalars(
                    select(WorkItem).where(
                        WorkItem.operation_id == operation.id,
                        WorkItem.status.in_(ACTIVE),
                    )
                ).all():
                    self.deliver_observation(
                        s,
                        s.get(SearchJob, item.job_id),
                        item,
                        result,
                        now,
                        operation.hard_expires_at,
                        fresh_until=fresh if eligible else None,
                    )
                operation.status = result.status.value
                self.trim_cache(s, now)
            attempt.outcome, attempt.finished_at = operation.status, now
            operation.lease_token = operation.leased_until = None
            return True

    def trim_cache(self, s, now):
        s.execute(delete(ProviderResultCache).where(ProviderResultCache.fresh_until <= now))
        entries = s.scalars(
            select(ProviderResultCache).order_by(ProviderResultCache.cached_at.desc())
        ).all()
        total = 0
        for index, entry in enumerate(entries):
            total += entry.byte_size
            if index >= self.cache_max_entries or total > self.cache_max_bytes:
                s.delete(entry)

    def sweep_operations(self, *, now, max_attempts):
        with write_session(self.engine) as s:
            self.trim_cache(s, now)
            for operation in s.scalars(
                select(ProviderOperation).where(ProviderOperation.status.in_(ACTIVE))
            ):
                expired = operation.status == "running" and operation.leased_until <= now
                budget = operation.deadline_at <= now or operation.hard_expires_at <= now
                if not expired and not budget:
                    continue
                if operation.status == "running":
                    attempt = s.scalar(
                        select(OperationAttempt).where(
                            OperationAttempt.operation_id == operation.id,
                            OperationAttempt.attempt == operation.attempts,
                        )
                    )
                    attempt.outcome = "budget_exhausted" if budget else "lease_expired"
                    attempt.finished_at = now
                terminal = budget or operation.attempts >= max_attempts
                operation.status = "failed_terminal" if terminal else "pending"
                operation.lease_token = operation.leased_until = None
                self.fail_subscribers(s, operation, "network_timeout", now, terminal=terminal)
            # Do not keep immutable query payload after its originating retention deadline.
            for operation in s.scalars(
                select(ProviderOperation).where(ProviderOperation.hard_expires_at <= now)
            ):
                operation.query_json = {}

    def reconcile_operations(self, s, registry, now):
        registrations = {r.provider.provider_id: r for r in registry}
        for operation in s.scalars(
            select(ProviderOperation).where(ProviderOperation.status.in_(ACTIVE))
        ):
            reg = registrations.get(operation.provider_id)
            if reg is None or reg.unavailable_reason or not reg.can_cache or not self.cache_enabled:
                operation.status = "failed_terminal"
                operation.lease_token = operation.leased_until = None
                self.fail_subscribers(s, operation, "unsupported_query", now)
        for entry in s.scalars(select(ProviderResultCache)):
            reg = registrations.get(entry.provider_id)
            if reg is None or reg.unavailable_reason or not reg.can_cache:
                s.delete(entry)
