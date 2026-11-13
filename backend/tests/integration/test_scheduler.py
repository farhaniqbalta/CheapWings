"""Production P4.9/P4.12 admission, physical capacity, protocol and recovery checks."""

import asyncio
import itertools
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from time import monotonic

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from cheapwings.application.job_runner import JobRunner
from cheapwings.config import Settings
from cheapwings.domain.evidence import ProviderFailure
from cheapwings.providers.base import SingleDateRouteQuery
from cheapwings.providers.fake import FakeProvider
from cheapwings.providers.octotrip import OctotripProvider
from cheapwings.providers.rate_limit import HttpStartGate, provider_failure, retry_after
from cheapwings.providers.registry import Registration, default_registry
from cheapwings.providers.swoop import BoundedCall
from cheapwings.storage.models import FareQuote, ProviderState, SearchJob, WorkItem
from cheapwings.storage.repository import Repository, now_ms


def small(query, n=1, offset=0):
    first = query.departure_date_from + timedelta(days=offset)
    return query.model_copy(
        update={
            "destinations": ["DPS"],
            "departure_date_from": first,
            "departure_date_through": first + timedelta(days=n - 1),
        }
    )


class Recorded(FakeProvider):
    def __init__(self, pid="recorded", latency=0.06):
        super().__init__(pid)
        self.latency = latency
        self.trace = []

    async def search(self, q):
        row = {"start": monotonic(), "date": q.departure_date}
        self.trace.append(row)
        try:
            await asyncio.sleep(self.latency)
            return await super().search(q)
        finally:
            row["end"] = monotonic()


def peak(rows):
    events = sorted([(r["start"], 1) for r in rows] + [(r["end"], -1) for r in rows])
    count = maximum = 0
    for _, delta in events:
        count += delta
        maximum = max(maximum, count)
    return maximum


async def drain(runner, repo, jobs):
    for _ in range(2000):
        await runner.tick()
        if (
            all(repo.get_job(j)[0].status not in ("queued", "running") for j in jobs)
            and not runner.tasks
        ):
            return
        await asyncio.sleep(0.002)
    raise AssertionError("worker did not drain")


@pytest.mark.parametrize("capacity", [5, 9])
@pytest.mark.parametrize(
    "provider_ids", [("one", "two", "three"), ("skiplagged", "swoop", "octotrip", "fli")]
)
async def test_fair_share_independent_sources_global_bound_spacing_and_progress(
    engine, query, capacity, provider_ids
):
    providers = [Recorded(pid, 0.12) for pid in provider_ids]
    regs = [Registration(p, minimum_interval_seconds=0.012) for p in providers]
    repo = Repository(engine, global_capacity=capacity)
    job = repo.create_job(small(query, 6), regs)
    runner = JobRunner(repo, regs, max_in_flight=capacity)
    try:
        await runner.tick()
        assert all(p.trace for p in providers)
        await asyncio.sleep(0.125)
        assert any(i.status.startswith("succeeded") for i in repo.get_job(job.id)[1])
        assert any(i.status != "succeeded_results" for i in repo.get_job(job.id)[1])
        await drain(runner, repo, [job.id])
        assert peak([r for p in providers for r in p.trace]) <= capacity
        # With every source busy, round-robin admission yields an even share of G.
        if capacity == 9:
            assert max(peak(p.trace) for p in providers) == 3
        for p in providers:
            assert peak(p.trace) <= 3 and len(p.trace) == 6
            assert all(b["start"] - a["start"] >= 0.012 for a, b in itertools.pairwise(p.trace))
    finally:
        await runner.close()


@pytest.mark.parametrize("cache", [False, True])
async def test_cancelled_late_429_persists_cooldown_without_quotes(engine, query, cache):
    started, release = asyncio.Event(), asyncio.Event()

    class Limited(FakeProvider):
        async def search(self, q):
            started.set()
            await release.wait()
            raise ProviderFailure("http_rate_limited", 60)

    reg = Registration(Limited(), minimum_interval_seconds=0)
    repo = Repository(engine, cache_enabled=cache)
    job = repo.create_job(small(query), [reg])
    runner = JobRunner(repo, [reg])
    try:
        await runner.tick()
        await started.wait()
        repo.cancel(job.id)
        release.set()
        await asyncio.gather(*runner.tasks)
        with Session(engine) as s:
            assert (
                s.get(ProviderState, reg.provider.provider_id).next_request_at >= now_ms() + 59000
            )
            assert s.scalar(select(func.count()).select_from(FareQuote)) == 0
        assert repo.get_job(job.id)[0].status == "cancelled"
    finally:
        release.set()
        await runner.close()


@pytest.mark.parametrize("blocking", [False, True])
@pytest.mark.parametrize("late_error", [False, True])
async def test_timeout_retains_capacity_and_rejects_late_results(
    engine, query, blocking, late_error
):
    release = threading.Event()
    released = asyncio.Event()

    class Late(FakeProvider):
        def __init__(self):
            super().__init__("late")
            if blocking:
                self.blocking = BoundedCall(3)

        async def search(self, q):
            if blocking:
                await self.blocking.run(release.wait)
            else:
                await released.wait()
            if late_error:
                raise ProviderFailure("http_rate_limited", 60)
            return await super().search(q)

    late, ready = Late(), Recorded("ready", 0.005)
    regs = [Registration(p, minimum_interval_seconds=0) for p in (late, ready)]
    repo = Repository(engine, global_capacity=1)
    job = repo.create_job(small(query), regs)
    runner = JobRunner(repo, regs, timeout_seconds=0.02, lease_seconds=1, max_attempts=1)
    try:
        await runner.tick()
        await asyncio.sleep(0.04)
        await runner.tick()
        assert runner.occupied() == 1 and not ready.trace
        assert any(i.last_error_code == "network_timeout" for i in repo.get_job(job.id)[1])
        release.set()
        released.set()
        await drain(runner, repo, [job.id])
        with Session(engine) as s:
            assert s.scalar(select(func.count()).select_from(FareQuote)) == 2  # ready only
            if late_error:
                assert s.get(ProviderState, "late").next_request_at >= now_ms() + 59000
    finally:
        release.set()
        released.set()
        await runner.close()


async def test_shutdown_waits_for_physical_threads_and_retains_feedback(engine, query):
    release = threading.Event()

    class Late(FakeProvider):
        def __init__(self):
            super().__init__()
            self.blocking = BoundedCall(3)

        def block(self):
            release.wait()
            raise ProviderFailure("http_rate_limited", 60)

        async def search(self, q):
            await self.blocking.run(self.block)

    p = Late()
    reg = Registration(p, minimum_interval_seconds=0)
    repo = Repository(engine)
    repo.create_job(small(query), [reg])
    runner = JobRunner(repo, [reg])
    closer = None
    try:
        await runner.tick()
        closer = asyncio.create_task(runner.close())
        await asyncio.sleep(0.02)
        assert not closer.done() and p.blocking.busy == 1
        release.set()
        await closer
        with Session(engine) as s:
            assert s.get(ProviderState, p.provider_id).next_request_at >= now_ms() + 59000
            assert s.scalar(select(func.count()).select_from(FareQuote)) == 0
    finally:
        release.set()
        if closer:
            await closer
        else:
            await runner.close()


@pytest.mark.parametrize("cache", [False, True])
def test_cooldown_between_claim_and_entry_defers_without_spending_attempt(engine, query, cache):
    reg = Registration(FakeProvider(), minimum_interval_seconds=0.1)
    repo = Repository(engine, cache_enabled=cache)
    job = repo.create_job(small(query), [reg])
    item, _ = repo.claim(reg)
    repo.record_provider_feedback(reg.provider.provider_id, "http_rate_limited", 60)
    assert not repo.mark_started(reg, item)
    assert repo.claim(reg) is None
    with Session(engine) as s:
        from cheapwings.storage.models import ProviderOperation

        row = s.get(ProviderOperation if cache else WorkItem, item.id)
        assert row.attempts == 0 and row.status == "retry_wait" and row.lease_token is None
    assert repo.get_job(job.id)[0].status in ("queued", "running")


@pytest.mark.parametrize(
    "large_cache,small_cache", [(False, True), (True, False), (True, True), (False, False)]
)
def test_durable_fairness_across_direct_and_shared_work(engine, query, large_cache, small_cache):
    reg = Registration(FakeProvider(), minimum_interval_seconds=0)
    repo = Repository(engine, cache_enabled=True, global_capacity=1)
    repo.create_job(small(query, 8), [replace(reg, can_cache=large_cache)])
    item, _ = repo.claim(reg)
    repo.finish(item.id, item.lease_token, error_code="auth_denied")
    little = repo.create_job(small(query, offset=20), [replace(reg, can_cache=small_cache)])
    # Recreate the repository to discard every in-memory scheduler cursor.
    restarted = Repository(engine, cache_enabled=True, global_capacity=1)
    served = []
    for _ in range(2):
        chosen, _ = restarted.claim(reg)
        with Session(engine) as session:
            primary = (
                session.get(WorkItem, chosen.primary_work_item_id)
                if chosen.id.startswith("fetch-")
                else chosen
            )
            served.append(primary.job_id)
        restarted.finish(chosen.id, chosen.lease_token, error_code="auth_denied")
    assert little.id in served  # at most one existing-job turn before the new job
    with Session(engine) as session:
        assert session.get(SearchJob, little.id).dispatch_sequence > 0


@pytest.mark.parametrize("cache", [False, True])
def test_global_atomic_claims_across_sources_and_shared_followers(engine, query, cache):
    regs = [
        Registration(FakeProvider(p), minimum_interval_seconds=0)
        for p in ("a", "b", "c")
    ]
    repo = Repository(engine, global_capacity=4, cache_enabled=cache)
    repo.create_job(small(query, 8), regs)
    if cache:
        repo.create_job(small(query, 8), regs)

    def claim(i):
        return Repository(engine, global_capacity=4, cache_enabled=cache).claim(regs[i % 3])

    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(claim, range(12)))
    won = [x[0] for x in results if x]
    # Exactly G distinct claims; with no per-provider ceiling one source may win them all.
    assert len(won) == 4 and len({x.id for x in won}) == 4


def test_actual_start_deadline_and_cooldown_survive_restart(engine, query, monkeypatch):
    import cheapwings.storage.repository as module

    reg = Registration(FakeProvider(), minimum_interval_seconds=1)
    repo = Repository(engine)
    repo.create_job(small(query, 2), [reg])
    start = now_ms()
    item, _ = repo.claim(reg, now=start)
    monkeypatch.setattr(module, "now_ms", lambda: start + 500)
    assert repo.mark_started(reg, item)
    repo.finish(item.id, item.lease_token, error_code="auth_denied", now=start + 600)
    restarted = Repository(engine)
    assert restarted.claim(reg, now=start + 1400) is None
    assert restarted.claim(reg, now=start + 1500)


async def test_bounded_swoop_executor_c3_has_actual_overlap_and_no_queue():
    release = threading.Event()
    pool = BoundedCall(3)
    tasks = [asyncio.create_task(pool.run(release.wait)) for _ in range(3)]
    try:
        await asyncio.sleep(0.02)
        assert pool.busy == 3
        with pytest.raises(ProviderFailure):
            await pool.run(lambda: None)
        tasks[0].cancel()
        await asyncio.gather(tasks[0], return_exceptions=True)
        assert pool.busy == 3  # cancellation cannot free a running thread
    finally:
        release.set()
        await asyncio.gather(*tasks, return_exceptions=True)
        await pool.drain()
        pool.close()


async def test_octotrip_gate_covers_initialization_across_three_sessions(monkeypatch):
    starts = []

    def respond(request):
        payload = json.loads(request.content)
        starts.append((monotonic(), payload["method"]))
        result = {} if payload["method"] == "initialize" else {"structuredContent": {"results": []}}
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": payload["id"], "result": result})

    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        "cheapwings.providers.octotrip.httpx.AsyncClient",
        lambda **kw: real_client(transport=httpx.MockTransport(respond), **kw),
    )
    provider = OctotripProvider()
    q = SingleDateRouteQuery("MEL", "DPS", date(2027, 3, 1), True, False, "USD")
    await asyncio.gather(*(provider.fetch(q) for _ in range(3)))
    assert len(starts) == 6
    assert sum(method == "initialize" for _, method in starts) == 3
    assert all(b[0] - a[0] >= 1.10 for a, b in itertools.pairwise(starts))


async def test_octotrip_429_stops_unsent_peer_http(monkeypatch):
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(429, headers={"Retry-After": "60"})

    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        "cheapwings.providers.octotrip.httpx.AsyncClient",
        lambda **kw: real_client(transport=httpx.MockTransport(respond), **kw),
    )
    provider = OctotripProvider(http_gate=HttpStartGate(0.005))
    q = SingleDateRouteQuery("MEL", "DPS", date(2027, 3, 1), True, False, "USD")
    outcomes = await asyncio.gather(*(provider.fetch(q) for _ in range(3)), return_exceptions=True)
    assert len(requests) == 1
    assert all(isinstance(e, ProviderFailure) and e.code == "http_rate_limited" for e in outcomes)


def test_retry_after_dates_nested_mcp_errors_and_defaults(monkeypatch):
    now = datetime(2026, 11, 11, tzinfo=UTC)
    assert retry_after("Wed, 11 Nov 2026 00:02:00 GMT", now=now) == 120
    assert retry_after("60", now=now) == 60
    assert retry_after("bad") == 60
    response = httpx.Response(
        429, headers={"Retry-After": "70"}, request=httpx.Request("POST", "https://example.invalid")
    )
    error = httpx.HTTPStatusError("redacted", request=response.request, response=response)
    failure = provider_failure(ExceptionGroup("outer", [ExceptionGroup("inner", [error])]))
    assert failure.code == "http_rate_limited" and failure.retry_after_seconds == 70
    settings = Settings.from_env()
    assert settings.worker_max_in_flight == 9
    assert not any("concurrency" in name for name in vars(settings))
    monkeypatch.setenv("ENABLED_PROVIDERS", "skiplagged,swoop,octotrip")
    registry = default_registry(Settings.from_env())
    assert not any(hasattr(r, "concurrency") for r in registry)
    assert [r.minimum_interval_seconds for r in registry] == [3, 0.1, 5, 0.25]
    # Adapter-intrinsic thread pools only: obsolete swoop keeps 3, Fli follows G.
    assert {
        r.provider.provider_id: r.provider.blocking.capacity
        for r in registry
        if hasattr(r.provider, "blocking")
    } == {"swoop": 3, "fli": 9}
    for reg in registry:
        if hasattr(reg.provider, "blocking"):
            reg.provider.blocking.close()


@pytest.mark.parametrize("cache", [False, True])
async def test_expired_lease_does_not_duplicate_still_running_work(engine, query, cache):
    release = asyncio.Event()
    starts = []

    class Held(FakeProvider):
        async def search(self, q):
            starts.append(monotonic())
            await release.wait()
            return await super().search(q)

    reg = Registration(Held(), minimum_interval_seconds=0)
    repo = Repository(engine, global_capacity=3, cache_enabled=cache)
    original = repo.create_job(small(query), [reg])
    runner = JobRunner(repo, [reg])
    try:
        await runner.tick()
        assert len(starts) == 1
        repo.sweep(now=now_ms() + 100000, max_attempts=1)
        jobs = [original.id]
        if cache:
            # Terminal old operation means admission creates a different fetch ID
            # for the same cache key. Its physical predecessor still owns that key.
            jobs.append(repo.create_job(small(query), [reg]).id)
        await runner.tick()
        assert len(starts) == 1 and runner.occupied() == 1
        release.set()
        await drain(runner, repo, jobs)
        assert len(starts) == (2 if cache else 1)
        with Session(engine) as s:
            assert s.scalar(select(func.count()).select_from(FareQuote)) == (2 if cache else 0)
    finally:
        release.set()
        await runner.close()


@pytest.mark.parametrize("cache", [False, True])
def test_cancel_before_adapter_entry_makes_no_upstream_call(engine, query, cache):
    reg = Registration(FakeProvider(), minimum_interval_seconds=0)
    repo = Repository(engine, cache_enabled=cache)
    job = repo.create_job(small(query), [reg])
    item, _ = repo.claim(reg)
    repo.cancel(job.id)
    assert not repo.mark_started(reg, item)
    assert repo.get_job(job.id)[0].status == "cancelled"


async def test_dispatch_database_failure_surfaces(engine, query):
    from cheapwings.application.job_runner import DispatchFailure

    class Broken(Repository):
        def mark_started(self, *args):
            raise RuntimeError("synthetic database failure")

    p = Recorded()
    reg = Registration(p, minimum_interval_seconds=0)
    repo = Broken(engine)
    repo.create_job(small(query), [reg])
    runner = JobRunner(repo, [reg])
    try:
        await runner.tick()
        await asyncio.gather(*runner.tasks, return_exceptions=True)
        with pytest.raises(DispatchFailure):
            await runner.tick()
        assert not p.trace
    finally:
        await runner.close()


def test_network_timeout_classification_in_mcp_group():
    exc = httpx.ReadTimeout("redacted")
    failure = provider_failure(ExceptionGroup("nested", [exc]))
    assert failure.code == "network_timeout"


def test_continuous_new_jobs_do_not_starve_already_served_jobs(engine, query):
    repo = Repository(engine, global_capacity=1)
    reg = Registration(FakeProvider(), minimum_interval_seconds=0)
    old = repo.create_job(small(query, 20), [reg])
    item, _ = repo.claim(reg)
    repo.finish(item.id, item.lease_token, error_code="auth_denied")
    old_turns = 0
    for i in range(12):
        repo.create_job(small(query, offset=30 + i), [reg], max_active=100)
        chosen, _ = repo.claim(reg)
        old_turns += chosen.job_id == old.id
        repo.finish(chosen.id, chosen.lease_token, error_code="auth_denied")
    assert old_turns >= 2


def test_upgrade_preserves_existing_jobs_leases_and_provider_deadlines(engine, query):
    from pathlib import Path

    from alembic import command
    from alembic.config import Config

    reg = Registration(FakeProvider(), minimum_interval_seconds=5)
    repo = Repository(engine)
    job = repo.create_job(small(query, 2), [reg])
    item, _ = repo.claim(reg)
    with Session(engine) as session:
        deadline = session.get(ProviderState, reg.provider.provider_id).next_request_at
    config = Config(str(Path(__file__).parents[2] / "alembic.ini"))
    config.attributes["database_url"] = str(engine.url)
    command.downgrade(config, "91f4b02a671c")
    command.upgrade(config, "head")
    recovered = Repository(engine)
    saved, items = recovered.get_job(job.id)
    assert saved.query_json == job.query_json and saved.deadline_at == job.deadline_at
    assert saved.dispatch_sequence == 0  # additive migration initializes legacy rows
    old = next(i for i in items if i.id == item.id)
    assert old.lease_token == item.lease_token and old.leased_until == item.leased_until
    with Session(engine) as session:
        assert session.get(ProviderState, reg.provider.provider_id).next_request_at == deadline
    assert recovered.claim(reg) is None


def test_reprice_job_is_not_starved_by_shared_search_backlog(engine, query):
    from cheapwings.storage.db import write_session

    reg = Registration(FakeProvider(), minimum_interval_seconds=0)
    repo = Repository(engine, global_capacity=1, cache_enabled=True)
    repo.create_job(small(query, 8), [reg])
    first, _ = repo.claim(reg)
    repo.finish(first.id, first.lease_token, error_code="auth_denied")
    little = repo.create_job(small(query, offset=20), [replace(reg, can_cache=False)])
    with write_session(engine) as session:
        item = session.scalar(select(WorkItem).where(WorkItem.job_id == little.id))
        item.work_type, item.target_key = "reprice", "synthetic-existing-quote"
    types = []
    for _ in range(2):
        item, _ = Repository(engine, global_capacity=1, cache_enabled=True).claim(reg)
        types.append(item.work_type)
        repo.finish(item.id, item.lease_token, error_code="auth_denied")
    assert "reprice" in types


async def test_scheduler_honors_actual_executor_capacity_when_registration_is_larger(engine, query):
    class SingleThread(FakeProvider):
        def __init__(self):
            super().__init__()
            self.blocking = BoundedCall(1)
            self.active = self.peak = 0

        def block(self):
            import time

            self.active += 1
            self.peak = max(self.peak, self.active)
            time.sleep(0.01)
            self.active -= 1

        async def search(self, q):
            await self.blocking.run(self.block)
            return await super().search(q)

    provider = SingleThread()
    reg = Registration(provider, minimum_interval_seconds=0)
    repo = Repository(engine)
    job = repo.create_job(small(query, 3), [reg])
    runner = JobRunner(repo, [reg])
    try:
        await drain(runner, repo, [job.id])
        assert provider.peak == 1
        assert all(
            i.attempts == 1 and i.status == "succeeded_results" for i in repo.get_job(job.id)[1]
        )
    finally:
        await runner.close()
