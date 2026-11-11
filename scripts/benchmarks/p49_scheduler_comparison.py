"""P4.9 CHECKPOINT-2 OFFLINE PROTOTYPES, not production scheduler implementation.

Uses production result execution, SQLite schema, cache admission, finish/sweep
and fencing. Only claim ordering/global admission and dispatch shape vary.
No real adapters or network transports are instantiated.
"""

import argparse
import asyncio
import heapq
import itertools
import json
import logging
import math
import random
import resource
import tempfile
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from time import monotonic
from uuid import uuid4

from alembic import command
from alembic.config import Config
from cheapwings.application.job_runner import JobRunner
from cheapwings.domain.query import SearchQuery
from cheapwings.providers.fake import FakeProvider
from cheapwings.providers.registry import Registration
from cheapwings.storage.db import database, write_session
from cheapwings.storage.models import (
    OperationAttempt,
    ProviderOperation,
    ProviderState,
    SearchJob,
    WorkAttempt,
    WorkItem,
)
from cheapwings.storage.repository import Repository, now_ms
from sqlalchemy import event, func, select
from sqlalchemy.orm import aliased

ACTIVE_JOBS = ("queued", "running")
ACTIVE_WORK = ("pending", "retry_wait", "running")
EXECUTION_KEY = ContextVar("p49_execution_key", default=None)


def quantile(values, q=0.95):
    return sorted(values)[max(0, math.ceil(q * len(values)) - 1)] if values else 0


def append_result(path, result):
    with path.open("a") as stream:
        stream.write(json.dumps(result, sort_keys=True) + "\n")


def recent_job_start(job_id):
    served = aliased(WorkItem)
    return (
        select(func.coalesce(func.max(served.started_at), 0))
        .where(served.job_id == job_id)
        .correlate_except(served)
        .scalar_subquery()
    )


class ReviewRepository(Repository):
    """Isolated copy of claim admission; inherited commit/cache/recovery unchanged.

    Fairness here is least-recently-dispatched active job, derived from durable
    WorkItem timestamps, including active subscribers of shared operations.
    Production adoption/precise fairness counter design needs owner approval.
    """

    def __init__(self, engine, *, global_capacity=6, fair=False, **kwargs):
        super().__init__(engine, **kwargs)
        self.global_capacity, self.fair = global_capacity, fair

    def claim(self, registration, *, lease_seconds=40, now=None):
        now = now if now is not None else now_ms()
        pid = registration.provider.provider_id
        if registration.unavailable_reason:
            return None
        with write_session(self.engine) as s:
            state = s.get(ProviderState, pid)
            if state is None:
                state = ProviderState(provider_id=pid, next_request_at=0)
                s.add(state)
            if state.next_request_at > now:
                return None
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
            if (
                sum(x.provider_id == pid for x in direct)
                + sum(x.provider_id == pid for x in operations)
                >= registration.concurrency
            ):
                return None
            operation = self.claim_operation(s, registration, now, lease_seconds)
            if operation:
                state.next_request_at = now + int(
                    registration.minimum_interval_seconds * 1000
                )
                return operation
            ordering = [SearchJob.created_at, WorkItem.departure_date, WorkItem.id]
            if self.fair:
                ordering.insert(0, recent_job_start(SearchJob.id))
            item = s.scalar(
                select(WorkItem)
                .join(SearchJob)
                .where(
                    WorkItem.provider_id == pid,
                    WorkItem.operation_id.is_(None),
                    WorkItem.status.in_(("pending", "retry_wait")),
                    WorkItem.next_attempt_at <= now,
                    SearchJob.status.in_(ACTIVE_JOBS),
                    SearchJob.cancel_requested.is_(False),
                    SearchJob.deadline_at > now,
                )
                .order_by(*ordering)
                .limit(1)
            )
            if item is None:
                return None
            item.status = "running"
            item.attempts += 1
            item.started_at = now
            if item.data_expires_at is None and registration.retention_seconds:
                item.data_expires_at = now + registration.retention_seconds * 1000
            item.lease_token = str(uuid4())
            item.leased_until = now + int(lease_seconds * 1000)
            s.add(
                WorkAttempt(work_item_id=item.id, attempt=item.attempts, started_at=now)
            )
            state.next_request_at = now + int(
                registration.minimum_interval_seconds * 1000
            )
            job = s.get(SearchJob, item.job_id)
            job.status = "running"
            job.updated_at = now
            return item, SearchQuery.model_validate(job.query_json)

    def claim_operation(self, s, registration, now, lease_seconds):
        if not self.fair:
            return super().claim_operation(s, registration, now, lease_seconds)
        subscriber = aliased(WorkItem)
        subscriber_job = aliased(SearchJob)
        priority = (
            select(func.min(recent_job_start(subscriber.job_id)))
            .select_from(subscriber)
            .join(subscriber_job, subscriber_job.id == subscriber.job_id)
            .where(
                subscriber.operation_id == ProviderOperation.id,
                subscriber.status.in_(ACTIVE_WORK),
                subscriber_job.status.in_(ACTIVE_JOBS),
                subscriber_job.cancel_requested.is_(False),
                subscriber_job.deadline_at > now,
            )
            .correlate(ProviderOperation)
            .scalar_subquery()
        )
        operation = s.scalar(
            select(ProviderOperation)
            .where(
                ProviderOperation.provider_id == registration.provider.provider_id,
                ProviderOperation.status.in_(("pending", "retry_wait")),
                ProviderOperation.next_attempt_at <= now,
                ProviderOperation.deadline_at > now,
            )
            .order_by(
                priority,
                ProviderOperation.created_at,
                ProviderOperation.departure_date,
                ProviderOperation.id,
            )
            .limit(1)
        )
        if operation is None:
            return None
        subscribers = s.scalars(
            select(WorkItem)
            .join(SearchJob)
            .where(
                WorkItem.operation_id == operation.id,
                WorkItem.status.in_(ACTIVE_WORK),
                SearchJob.status.in_(ACTIVE_JOBS),
                SearchJob.cancel_requested.is_(False),
                SearchJob.deadline_at > now,
            )
        ).all()
        if not subscribers:
            operation.status = "cancelled"
            return None
        from cheapwings.storage.cache import cache_key

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
            OperationAttempt(
                operation_id=operation.id, attempt=operation.attempts, started_at=now
            )
        )
        for item in subscribers:
            item.status = "running"
            item.started_at = item.started_at or now
            job = s.get(SearchJob, item.job_id)
            job.status = "running"
            job.updated_at = now
        return operation, SearchQuery.model_validate(operation.query_json)


class TimedFake(FakeProvider):
    def __init__(self, pid, latencies, trace):
        super().__init__(provider_id=pid)
        self.latencies, self.trace, self.count = latencies, trace, 0

    @property
    def physical_keys(self):
        return set()

    async def search(self, q):
        row = {
            "provider": self.provider_id,
            "start": monotonic(),
            "query": f"{q.origin}-{q.destination}-{q.departure_date}",
        }
        latency = self.latencies[self.count % len(self.latencies)]
        self.count += 1
        self.trace.append(row)
        try:
            await asyncio.sleep(latency)
            return await super().search(q)
        finally:
            row["end"] = monotonic()


class ReviewDispatcher(JobRunner):
    """A0=bounded existing-style FIFO; A=fair independent tasks; B=fixed workers.

    A and B intentionally share the same eligibility selector and fair queue.
    A creates only active tasks. B uses bounded one-item worker mailboxes, never
    hands an ineligible job to a worker to sleep through a cooldown.
    """

    def __init__(
        self, repo, registry, *, variant="A", global_capacity=6, housekeeping=0.1
    ):
        super().__init__(repo, registry)
        self.variant, self.global_capacity = variant, global_capacity
        self.active = {}
        self.local_next = {}
        self.start_pending = set()
        self.cursor = 0
        self.changed = asyncio.Event()
        self.mailboxes = [asyncio.Queue(maxsize=1) for _ in range(global_capacity)]
        self.idle = set(range(global_capacity))
        self.workers = []
        self.last_maintenance = 0
        self.housekeeping = housekeeping
        self.dispatches = []
        self.busy_integral = 0
        self.last_sample = monotonic()
        self.peak = 0
        self.ticks = []

    def occupied(self, pid=None):
        keys = {key for key, p in self.active.items() if pid is None or p == pid}
        for registration in self.registry:
            if pid is None or registration.provider.provider_id == pid:
                keys.update(getattr(registration.provider, "physical_keys", set()))
        return len(keys)

    async def execute(self, registration, item, query):
        pid = registration.provider.provider_id
        self.start_pending.discard(pid)
        self.local_next[pid] = monotonic() + registration.minimum_interval_seconds
        self.dispatches.append(
            {
                "job": item.job_id if hasattr(item, "job_id") else None,
                "operation": item.id,
                "provider": pid,
                "start": monotonic(),
            }
        )
        token = EXECUTION_KEY.set(item.id)
        try:
            await super().execute(registration, item, query)
        finally:
            EXECUTION_KEY.reset(token)
            self.active.pop(item.id, None)
            self.changed.set()

    async def worker(self, index):
        while True:
            payload = await self.mailboxes[index].get()
            try:
                await self.execute(*payload)
            finally:
                self.idle.add(index)
                self.changed.set()

    async def tick(self):
        begin = monotonic()
        self.busy_integral += (begin - self.last_sample) * self.occupied()
        self.last_sample = begin
        for task in list(self.tasks):
            if task.done():
                self.tasks.remove(task)
                task.result()
        for worker in self.workers:
            if worker.done():
                worker.result()
                raise RuntimeError("Prototype worker exited unexpectedly")
        if self.variant == "B" and not self.workers:
            self.workers = [
                asyncio.create_task(self.worker(i)) for i in range(self.global_capacity)
            ]
        if begin - self.last_maintenance >= self.housekeeping:
            self.repo.purge_expired()
            self.repo.reconcile_registry(self.registry)
            self.repo.sweep()
            self.repo.schedule_verification()
            self.last_maintenance = begin
        while self.occupied() < self.global_capacity:
            started = False
            indices = list(range(len(self.registry)))
            if self.variant != "A0":
                indices = indices[self.cursor :] + indices[: self.cursor]
            for index in indices:
                reg = self.registry[index]
                pid = reg.provider.provider_id
                if self.occupied(pid) >= reg.concurrency:
                    continue
                if self.variant != "A0" and (
                    (pid in self.start_pending and reg.minimum_interval_seconds > 0)
                    or self.local_next.get(pid, 0) > monotonic()
                ):
                    continue
                if self.variant == "B" and not self.idle:
                    continue
                claimed = self.repo.claim(
                    reg,
                    lease_seconds=max(
                        self.lease_seconds,
                        (reg.timeout_seconds or self.timeout_seconds) + 10,
                    ),
                )
                if claimed is None:
                    continue
                item, q = claimed
                self.active[item.id] = pid
                self.peak = max(self.peak, self.occupied())
                self.start_pending.add(pid)
                if self.variant == "B":
                    slot = min(self.idle)
                    self.idle.remove(slot)
                    self.mailboxes[slot].put_nowait((reg, item, q))
                else:
                    self.tasks.add(asyncio.create_task(self.execute(reg, item, q)))
                if self.variant != "A0":
                    self.cursor = (index + 1) % len(self.registry)
                started = True
                break
            if not started:
                break
        await asyncio.sleep(0)
        await asyncio.sleep(0)  # production execute now enters a shielded child task
        self.ticks.append(monotonic() - begin)

    async def pause(self):
        if self.variant == "A0":
            await asyncio.sleep(0.1)
            return
        if self.changed.is_set():
            self.changed.clear()
            await asyncio.sleep(0)
            return
        delay = max(0.001, self.housekeeping - (monotonic() - self.last_maintenance))
        deadlines = [
            value - monotonic()
            for value in self.local_next.values()
            if value > monotonic()
        ]
        if deadlines:
            delay = min(delay, min(deadlines))
        try:
            await asyncio.wait_for(self.changed.wait(), delay)
        except TimeoutError:
            pass

    async def close(self):
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers = []
        await super().close()


class MeasuredProduction(JobRunner):
    """Instrument the selected scheduler without changing its dispatch behavior."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ticks = []

    @property
    def active(self):
        return self.task_providers

    async def tick(self):
        begin = monotonic()
        await super().tick()
        self.ticks.append(monotonic() - begin)


def migrated(path):
    cfg = Config("backend/alembic.ini")
    cfg.attributes["database_url"] = "sqlite:///" + str(path)
    command.upgrade(cfg, "head")
    return database(cfg.attributes["database_url"])


def replay_latencies():
    """Read committed P4.8 observations; never re-run its adapters/experiments."""
    text = Path("docs/log/p4.8-throughput-experiment.md").read_text()
    cohorts = {
        "skiplagged": "initial / skiplagged-1-c2-i1",
        "swoop": "swoop retry / swoop-1-c2-i0.1",
        "octotrip": "matched / octotrip-2-c2-i5",
    }
    values = {p: [] for p in cohorts}
    for line in text.splitlines():
        if not line.startswith("| "):
            continue
        fields = [x.strip() for x in line.strip("|").split("|")]
        for p, cohort in cohorts.items():
            if fields[0] == cohort:
                values[p].append(float(fields[5 if p == "swoop" else 6]))
    assert all(len(x) == 8 for x in values.values()), values
    return values


@dataclass
class Scenario:
    name: str
    counts: tuple
    latencies: tuple
    intervals: tuple
    capacities: tuple = (2, 2, 2)
    global_capacity: int = 6
    cooldown: float = 0
    small_jobs: int = 0
    cache: bool = False


def scenarios():
    live = replay_latencies()
    lat = tuple(
        [x * 0.05 for x in live[p]] for p in ("skiplagged", "swoop", "octotrip")
    )
    return [
        Scenario(
            "p48_like_15s_c1_scaled", (8, 8, 8), lat, (0.75, 0.75, 0.75), (1, 1, 1), 3
        ),
        Scenario("candidate_replay_scaled", (8, 8, 8), lat, (0.05, 0.005, 0.25)),
        Scenario(
            "owner_c3_replay_scaled", (8, 8, 8), lat, (0.05, 0.005, 0.25), (3, 3, 3), 9
        ),
        Scenario("large_fast", (32, 32, 32), ([0.025], [0.025], [0.025]), (0, 0, 0)),
        Scenario(
            "large_quarter_second",
            (32, 32, 32),
            ([0.25], [0.25], [0.25]),
            (0, 0, 0),
        ),
        Scenario(
            "tight_global_budget",
            (16, 4, 8),
            ([0.025], [0.01], [0.2]),
            (0, 0, 0.03),
            global_capacity=2,
        ),
        Scenario(
            "cooldown_independence",
            (8, 8, 4),
            ([0.04], [0.02], [0.1]),
            (0.01, 0.01, 0.02),
            global_capacity=2,
            cooldown=0.35,
        ),
        Scenario(
            "idle_provider",
            (0, 24, 8),
            ([0.1], [0.025], [0.1]),
            (0, 0, 0.01),
            global_capacity=3,
        ),
        Scenario(
            "job_fairness",
            (48, 0, 0),
            ([0.015], [0.01], [0.01]),
            (0, 0, 0),
            (1, 1, 1),
            1,
            small_jobs=3,
        ),
        Scenario(
            "shared_cache", (8, 8, 0), ([0.025], [0.025], [0.1]), (0, 0, 0), cache=True
        ),
    ]


async def run_trial(spec, variant, repeat, directory):
    engine = migrated(directory / f"{spec.name}-{variant}-{repeat}.db")
    trace = []
    pids = ("skiplagged", "swoop", "octotrip")
    providers = [TimedFake(p, spec.latencies[i], trace) for i, p in enumerate(pids)]
    regs = [
        Registration(
            p,
            concurrency=spec.capacities[i],
            minimum_interval_seconds=spec.intervals[i],
        )
        for i, p in enumerate(providers)
    ]
    repo = (
        Repository(
            engine, global_capacity=spec.global_capacity, cache_enabled=spec.cache
        )
        if variant == "P49"
        else ReviewRepository(
            engine,
            global_capacity=spec.global_capacity,
            fair=variant != "A0",
            cache_enabled=spec.cache,
        )
    )
    jobs = []
    admitted = {}
    labels = {}

    def admit(n, reg, label, offset=0):
        q = SearchQuery(
            display_currency="USD",
            origins=["MEL"],
            destinations=["DPS", "SIN"] if n % 2 == 0 else ["DPS"],
            departure_date_from=date(2027, 2, 1) + timedelta(days=offset),
            departure_date_through=date(2027, 2, 1)
            + timedelta(days=offset + (n // 2 if n % 2 == 0 else n) - 1),
        )
        job = repo.create_job(
            q,
            [reg],
            max_active=100,
            max_hourly=1000,
            max_requests=1000,
            max_active_requests=100,
        )
        jobs.append(job.id)
        admitted[job.id] = monotonic()
        labels[job.id] = label
        return job

    begin = monotonic()
    for i, n in enumerate(spec.counts):
        if n:
            admit(n, regs[i], "bulk-" + pids[i])
    if spec.cache:
        admit(spec.counts[0], regs[0], "follower")
    if spec.cooldown:
        with write_session(engine) as session:
            session.add(
                ProviderState(
                    provider_id="octotrip",
                    next_request_at=now_ms() + int(spec.cooldown * 1000),
                )
            )
    runner = (
        MeasuredProduction(repo, regs, max_in_flight=spec.global_capacity)
        if variant == "P49"
        else ReviewDispatcher(
            repo, regs, variant=variant, global_capacity=spec.global_capacity
        )
    )
    sql = []
    lags = []
    completion = {}
    first = {}
    small = False

    def sql_start(conn, cursor, statement, parameters, context, many):
        context.p49_begin = monotonic()

    def sql_end(conn, cursor, statement, parameters, context, many):
        sql.append(monotonic() - context.p49_begin)

    event.listen(engine, "before_cursor_execute", sql_start)
    event.listen(engine, "after_cursor_execute", sql_end)

    async def monitor():
        while True:
            target = monotonic() + 0.005
            await asyncio.sleep(0.005)
            lags.append(max(0, monotonic() - target))

    task = asyncio.create_task(monitor())
    cpu_start = resource.getrusage(resource.RUSAGE_SELF)
    try:
        while True:
            await runner.tick()
            if spec.small_jobs and not small and trace:
                for j in range(spec.small_jobs):
                    admit(1, regs[0], "small", offset=80 + j)
                small = True
            terminal = True
            for job in jobs:
                state, items = repo.get_job(job)
                if any(x.status.startswith("succeeded") for x in items):
                    first.setdefault(job, monotonic())
                if state.status in ACTIVE_JOBS:
                    terminal = False
                else:
                    completion.setdefault(job, monotonic())
            if terminal and not runner.active:
                break
            await runner.pause()
        end = monotonic()
        items = [x for job in jobs for x in repo.get_job(job)[1]]
        assert all(x.status.startswith("succeeded") for x in items)
        lat = [r["end"] - r["start"] for r in trace]
        spans = sorted(
            [(r["start"], 1) for r in trace] + [(r["end"], -1) for r in trace]
        )
        active = peak = 0
        integral = 0
        previous = begin
        for stamp, change in spans:
            integral += active * (stamp - previous)
            previous = stamp
            active += change
            peak = max(peak, active)
        cpu_end = resource.getrusage(resource.RUSAGE_SELF)
        cpu = (
            cpu_end.ru_utime
            + cpu_end.ru_stime
            - cpu_start.ru_utime
            - cpu_start.ru_stime
        )
        provider_metrics = {}
        for i, pid in enumerate(pids):
            calls = [r for r in trace if r["provider"] == pid]
            gaps = [b["start"] - a["start"] for a, b in itertools.pairwise(calls)]
            slots = [begin] * spec.capacities[i]
            last = begin - spec.intervals[i]
            delays = []
            for call in calls:
                slot = heapq.heappop(slots)
                eligible = max(
                    slot, last + spec.intervals[i] if spec.intervals[i] else begin
                )
                delays.append(max(0, call["start"] - eligible))
                last = call["start"]
                heapq.heappush(slots, call["end"])
            provider_metrics[pid] = {
                "calls": len(calls),
                "latency_p50_s": quantile([c["end"] - c["start"] for c in calls], 0.5),
                "latency_p95_s": quantile([c["end"] - c["start"] for c in calls]),
                "minimum_gap_s": min(gaps, default=None),
                "dispatch_delay_p95_s": quantile(delays),
                "first_s": min((x["start"] - begin for x in calls), default=None),
            }
        return {
            "scenario": spec.name,
            "variant": variant,
            "repeat": repeat,
            "global_capacity": spec.global_capacity,
            "counts": spec.counts,
            "intervals": spec.intervals,
            "provider_capacities": spec.capacities,
            "elapsed_s": end - begin,
            "calls": len(trace),
            "successes": len(items),
            "throughput_per_min": 60 * len(trace) / (end - begin),
            "first_result_s": min(first.values()) - begin,
            "latency_p50_s": quantile(lat, 0.5),
            "latency_p95_s": quantile(lat),
            "slot_utilization": integral / (spec.global_capacity * (end - begin)),
            "peak_active": peak,
            "tick_p95_s": quantile(runner.ticks),
            "loop_lag_p95_s": quantile(lags),
            "loop_lag_max_s": max(lags, default=0),
            "sql_count": len(sql),
            "sql_p95_s": quantile(sql),
            "cpu_seconds": cpu,
            "cpu_one_core_percent": 100 * cpu / (end - begin),
            "peak_rss_bytes": cpu_end.ru_maxrss,
            "small_job_first_p95_s": quantile(
                [first[j] - admitted[j] for j in jobs if labels[j] == "small"]
            ),
            "provider_metrics": provider_metrics,
            "trace": trace,
        }
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        await runner.close()
        engine.dispose()


async def main(args):
    logging.disable(logging.CRITICAL)
    output = Path(args.output)
    if output.exists():
        raise SystemExit("Output exists")
    with tempfile.TemporaryDirectory(prefix="p49-review-") as directory:
        for repeat in range(args.repeats):
            for spec in scenarios():
                if args.scenario and spec.name not in args.scenario:
                    continue
                order = list(args.variant or ["A0", "A", "B"])
                random.Random(49 + repeat).shuffle(order)
                for variant in order:
                    result = await run_trial(spec, variant, repeat, Path(directory))
                    append_result(output, result)
                    print(
                        json.dumps(
                            {
                                k: v
                                for k, v in result.items()
                                if k not in ("trace", "provider_metrics")
                            },
                            sort_keys=True,
                        ),
                        flush=True,
                    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--variant", action="append", choices=["A0", "A", "B", "P49"])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument(
        "--scenario", action="append", help="Run only this scenario (repeatable)"
    )
    asyncio.run(main(parser.parse_args()))
