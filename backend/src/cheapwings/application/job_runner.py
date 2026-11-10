"""One queue owner; short DB claims enforce global adapter concurrency and pacing."""

import asyncio
import logging
from datetime import date
from time import monotonic

from cheapwings.domain.coverage import WorkStatus
from cheapwings.domain.evidence import ProviderFailure
from cheapwings.providers.base import SingleDateRouteQuery

log = logging.getLogger(__name__)


class JobRunner:
    def __init__(self, repo, registry, *, timeout_seconds=30, lease_seconds=40, max_attempts=3):
        if lease_seconds <= timeout_seconds or max_attempts < 1:
            raise ValueError("Lease must exceed call timeout; max_attempts must be positive")
        self.repo, self.registry = repo, registry
        self.timeout_seconds, self.lease_seconds = timeout_seconds, lease_seconds
        self.max_attempts = max_attempts
        self.tasks = set()
        self.task_providers = {}

    async def execute(self, registration, item, query):
        request = SingleDateRouteQuery(
            item.origin,
            item.destination,
            date.fromisoformat(item.departure_date),
            query.include_basic_economy,
            query.include_hidden_city,
            query.display_currency,
            query.point_of_sale_country,
        )
        started = monotonic()
        result = None
        error, retry_after = None, 0
        try:
            async with asyncio.timeout(registration.timeout_seconds or self.timeout_seconds):
                if item.work_type == "reprice":
                    result = await registration.provider.reprice(self.repo.reprice_request(item))
                else:
                    result = await registration.provider.search(request)
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
        except TimeoutError:
            error = "network_timeout"
        except ProviderFailure as exc:
            error, retry_after = exc.code, exc.retry_after_seconds
        except asyncio.CancelledError:
            raise  # abrupt stop leaves durable lease for restart recovery
        except Exception:  # noqa: BLE001 - adapter isolation; no raw exception persisted
            error = "provider_unavailable"  # exception text may contain source secrets
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
        log.info(
            "work_finished job_id=%s work_item_id=%s provider=%s attempt=%s error=%s elapsed_ms=%s",
            item.job_id,
            item.id,
            item.provider_id,
            item.attempts,
            error,
            int((monotonic() - started) * 1000),
        )

    async def tick(self):
        for task in list(self.tasks):
            if task.done():
                self.tasks.remove(task)
                self.task_providers.pop(task)
                task.result()  # surface database/programming errors; never silently drop them
        self.repo.purge_expired()
        self.repo.reconcile_registry(self.registry)
        self.repo.sweep(max_attempts=self.max_attempts)
        self.repo.schedule_verification()
        for registration in self.registry:
            active = sum(
                p == registration.provider.provider_id for p in self.task_providers.values()
            )
            for _ in range(max(0, registration.concurrency - active)):
                claimed = self.repo.claim(
                    registration,
                    lease_seconds=max(
                        self.lease_seconds,
                        (registration.timeout_seconds or self.timeout_seconds) + 10,
                    ),
                )
                if claimed is None:
                    break
                item, query = claimed
                task = asyncio.create_task(self.execute(registration, item, query))
                self.tasks.add(task)
                self.task_providers[task] = registration.provider.provider_id
        await asyncio.sleep(0)

    async def run(self):
        try:
            while True:
                await self.tick()
                await asyncio.sleep(0.1)
        finally:
            await self.close()

    async def close(self):
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()
        self.task_providers.clear()
        for registration in self.registry:
            blocking = getattr(registration.provider, "blocking", None)
            if blocking:
                blocking.close()
