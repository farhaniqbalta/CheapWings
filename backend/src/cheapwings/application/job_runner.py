"""One durable queue owner; one shared global pool with independent provider pacing."""

import asyncio
import logging
from datetime import date
from time import monotonic

from cheapwings.domain.coverage import WorkStatus
from cheapwings.domain.evidence import ProviderFailure
from cheapwings.providers.base import SingleDateRouteQuery
from cheapwings.providers.rate_limit import provider_failure

log = logging.getLogger(__name__)


class DispatchDeferred(Exception):
    """The claim became ineligible before adapter entry; no upstream call made."""


class DispatchFailure(RuntimeError):
    """A persistence failure must surface, never become a provider retry."""


class JobRunner:
    def __init__(
        self,
        repo,
        registry,
        *,
        timeout_seconds=30,
        lease_seconds=40,
        max_attempts=3,
        max_in_flight=None,
    ):
        if lease_seconds <= timeout_seconds or max_attempts < 1:
            raise ValueError("Lease must exceed call timeout; max_attempts must be positive")
        self.repo, self.registry = repo, registry
        self.timeout_seconds, self.lease_seconds = timeout_seconds, lease_seconds
        self.max_attempts = max_attempts
        self.max_in_flight = max_in_flight if max_in_flight is not None else repo.global_capacity
        if self.max_in_flight < 1:
            raise ValueError("Global capacity must be positive")
        repo.global_capacity = self.max_in_flight
        self.tasks = set()
        self.task_providers = {}
        self.task_items = {}
        self._starting = set()
        self._next_start = {}
        self._changed = asyncio.Event()
        self._cursor = 0
        self._maintenance_at = 0
        self._closing = False

    async def invoke(self, registration, item, request):
        pid = registration.provider.provider_id
        try:
            allowed = self.repo.mark_started(registration, item)
        except Exception as exc:
            raise DispatchFailure("Unable to authorize dispatch") from exc
        if not allowed:
            self._starting.discard(pid)
            raise DispatchDeferred
        # No await between this timestamp and entering the adapter. The HTTP
        # protocol gate, when required, is separately inside the provider.
        self._next_start[pid] = monotonic() + registration.minimum_interval_seconds
        self._starting.discard(pid)
        if item.work_type == "reprice":
            return await registration.provider.reprice(request)
        return await registration.provider.search(request)

    @staticmethod
    def validate_result(item, request, result):
        if item.work_type != "reprice":
            if result.provider_id != item.provider_id or result.requested != request:
                raise ProviderFailure("schema_changed")
            if result.status == WorkStatus.FAILED_TERMINAL:
                raise ProviderFailure(result.error_code.value)
            if result.status not in (WorkStatus.SUCCEEDED_EMPTY, WorkStatus.SUCCEEDED_RESULTS):
                raise ProviderFailure("schema_changed")
            for offers in result.offers_by_itinerary_index:
                if any(o.provider_id != item.provider_id for o in offers):
                    raise ProviderFailure("schema_changed")

    async def execute(self, registration, item, query):
        request = (
            self.repo.reprice_request(item)
            if item.work_type == "reprice"
            else SingleDateRouteQuery(
                item.origin,
                item.destination,
                date.fromisoformat(item.departure_date),
                query.include_basic_economy,
                query.include_hidden_city,
                query.display_currency,
                query.point_of_sale_country,
            )
        )
        started = monotonic()
        result, error, retry_after = None, None, 0
        call = asyncio.create_task(self.invoke(registration, item, request))
        try:
            try:
                # Shielding is deliberate: a timeout is not proof that actual
                # I/O stopped. This execution task retains its capacity until it does.
                result = await asyncio.wait_for(
                    asyncio.shield(call), registration.timeout_seconds or self.timeout_seconds
                )
                self.validate_result(item, request, result)
            except DispatchDeferred:
                return
            except DispatchFailure:
                raise
            except TimeoutError:
                error = "network_timeout"
            except Exception as exc:  # noqa: BLE001 - provider isolation, no raw errors retained
                failure = provider_failure(exc)
                error = failure.code if failure else "provider_unavailable"
                retry_after = failure.retry_after_seconds if failure else 0
            try:
                self.repo.finish(
                    item.id,
                    item.lease_token,
                    result,
                    error_code=error,
                    retry_after_seconds=retry_after,
                    max_attempts=self.max_attempts,
                )
            except (ValueError, TypeError, AttributeError):
                self.repo.finish(
                    item.id,
                    item.lease_token,
                    error_code="schema_changed",
                    max_attempts=self.max_attempts,
                )
            self._changed.set()  # progressive results; physical work can still be running
            if not call.done():
                try:
                    await asyncio.shield(call)
                except Exception as exc:  # noqa: BLE001 - provider isolation, no raw errors retained
                    failure = provider_failure(exc)
                    if failure:
                        self.repo.record_provider_feedback(
                            item.provider_id, failure.code, failure.retry_after_seconds
                        )
                # Late success is intentionally discarded, never committed.
        except asyncio.CancelledError:
            call.cancel()
            await asyncio.gather(call, return_exceptions=True)
            raise  # durable lease/fence handles abrupt shutdown
        finally:
            if not call.done():
                call.cancel()
                await asyncio.gather(call, return_exceptions=True)
            self._starting.discard(registration.provider.provider_id)
            self._changed.set()
            log.info(
                "work_finished job_id=%s work_item_id=%s provider=%s attempt=%s error=%s elapsed_ms=%s",
                item.job_id,
                item.id,
                item.provider_id,
                item.attempts,
                error,
                int((monotonic() - started) * 1000),
            )

    def occupied(self, pid=None):
        total = 0
        for reg in self.registry:
            provider_id = reg.provider.provider_id
            if pid is not None and pid != provider_id:
                continue
            # Finished tasks remain counted until their exception is collected.
            logical = sum(p == provider_id for p in self.task_providers.values())
            blocking = getattr(reg.provider, "blocking", None)
            total += max(logical, blocking.busy if blocking else 0)
        return total

    async def tick(self):
        for task in list(self.tasks):
            if task.done():
                self.tasks.remove(task)
                self.task_providers.pop(task)
                self.task_items.pop(task)
                task.result()
        if self._closing:
            return
        if monotonic() >= self._maintenance_at:
            self.repo.purge_expired()
            self.repo.reconcile_registry(self.registry)
            self.repo.sweep(max_attempts=self.max_attempts)
            self.repo.schedule_verification()
            self._maintenance_at = monotonic() + 0.1
        while self.occupied() < self.max_in_flight:
            dispatched = False
            for offset in range(len(self.registry)):
                index = (self._cursor + offset) % len(self.registry)
                reg = self.registry[index]
                pid = reg.provider.provider_id
                # No scheduler per-provider ceiling: providers share the global
                # budget. Only an adapter's real thread pool may refuse (no queueing);
                # occupied() also counts dispatched tasks not yet holding a thread.
                blocking = getattr(reg.provider, "blocking", None)
                if blocking and self.occupied(pid) >= blocking.capacity:
                    continue
                if reg.minimum_interval_seconds > 0 and (
                    pid in self._starting or self._next_start.get(pid, 0) > monotonic()
                ):
                    continue
                claimed = self.repo.claim(
                    reg,
                    exclude_ids=[item.id for item in self.task_items.values()],
                    exclude_cache_keys=[
                        item.cache_key
                        for item in self.task_items.values()
                        if hasattr(item, "cache_key")
                    ],
                    lease_seconds=max(
                        self.lease_seconds, (reg.timeout_seconds or self.timeout_seconds) + 10
                    ),
                )
                if claimed is None:
                    continue
                item, query = claimed
                self._starting.add(pid)
                task = asyncio.create_task(self.execute(reg, item, query))
                self.tasks.add(task)
                self.task_providers[task] = pid
                self.task_items[task] = item
                task.add_done_callback(lambda _: self._changed.set())
                self._cursor = (index + 1) % len(self.registry)
                dispatched = True
                break
            if not dispatched:
                break
        # Let newly claimed tasks enter their adapters before returning.
        await asyncio.sleep(0)
        await asyncio.sleep(0)

    async def pause(self):
        if self._changed.is_set():
            self._changed.clear()
            await asyncio.sleep(0)
            return
        delay = max(0.001, self._maintenance_at - monotonic())
        deadlines = [t - monotonic() for t in self._next_start.values() if t > monotonic()]
        if deadlines:
            delay = min(delay, min(deadlines))
        try:
            await asyncio.wait_for(self._changed.wait(), delay)
        except TimeoutError:
            pass

    async def run(self):
        try:
            while True:
                await self.tick()
                await self.pause()
        finally:
            await self.close()

    async def close(self):
        self._closing = True
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        # Keep the worker ownership lock until every real thread has ended.
        # Uninterruptible work may need owner-initiated process termination.
        for reg in self.registry:
            blocking = getattr(reg.provider, "blocking", None)
            if blocking:
                outcomes = await blocking.drain()
                for outcome in outcomes:
                    if isinstance(outcome, BaseException):
                        failure = provider_failure(outcome)
                        if failure:
                            self.repo.record_provider_feedback(
                                reg.provider.provider_id, failure.code, failure.retry_after_seconds
                            )
                blocking.close()
        self.tasks.clear()
        self.task_providers.clear()
        self.task_items.clear()
