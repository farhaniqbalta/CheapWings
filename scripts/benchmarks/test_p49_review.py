"""Offline acceptance checks for checkpoint-2 prototypes, never live providers."""
# Imported pytest fixtures intentionally share the test argument names.
# ruff: noqa: F811

import asyncio
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "backend/tests/integration")
)
import itertools

from cheapwings.domain.query import SearchQuery
from cheapwings.providers.fake import FakeProvider
from cheapwings.providers.registry import Registration
from cheapwings.providers.swoop import BoundedCall
from cheapwings.storage.db import write_session
from cheapwings.storage.models import FareQuote, ProviderState
from cheapwings.storage.repository import now_ms
from p49_scheduler_comparison import (
    EXECUTION_KEY,
    ReviewDispatcher,
    ReviewRepository,
    TimedFake,
)
from test_storage import engine  # noqa: F401


def query(n=3, offset=0):
    first = date(2027, 3, 1) + timedelta(days=offset)
    return SearchQuery(
        origins=["MEL"],
        destinations=["DPS"],
        departure_date_from=first,
        departure_date_through=first + timedelta(days=n - 1),
        display_currency="USD",
    )


async def drain(runner, repo, job_ids):
    for _ in range(1000):
        await runner.tick()
        if (
            all(repo.get_job(j)[0].status not in ("queued", "running") for j in job_ids)
            and not runner.active
        ):
            return
        await asyncio.sleep(0.002)
    raise AssertionError("prototype did not drain")


def max_overlap(trace, pid=None):
    rows = [r for r in trace if pid is None or r["provider"] == pid]
    events = sorted([(r["start"], 1) for r in rows] + [(r["end"], -1) for r in rows])
    active = peak = 0
    for _, delta in events:
        active += delta
        peak = max(peak, active)
    return peak


@pytest.mark.parametrize("variant", ["A", "B"])
@pytest.mark.asyncio
async def test_independent_sources_global_capacity_and_progressive_commit(
    engine, variant
):
    trace = []
    providers = [
        TimedFake(name, [latency], trace)
        for name, latency in [("fast", 0.02), ("medium", 0.04), ("slow", 0.09)]
    ]
    regs = [
        Registration(p, minimum_interval_seconds=0.01) for p in providers
    ]
    repo = ReviewRepository(engine, global_capacity=3, fair=True)
    job = repo.create_job(query(), regs)
    runner = ReviewDispatcher(repo, regs, variant=variant, global_capacity=3)
    try:
        await runner.tick()
        assert len(trace) == 3 and len({x["provider"] for x in trace}) == 3
        await asyncio.sleep(0.03)
        items = repo.get_job(job.id)[1]
        assert any(i.status.startswith("succeeded") for i in items)
        assert any(i.status == "running" for i in items)
        await drain(runner, repo, [job.id])
        assert max_overlap(trace) <= 3
        assert all(max_overlap(trace, p.provider_id) <= 2 for p in providers)
        with Session(engine) as s:
            assert s.scalar(select(func.count()).select_from(FareQuote)) == 18
    finally:
        await runner.close()


@pytest.mark.parametrize("variant", ["A", "B"])
@pytest.mark.asyncio
async def test_within_provider_overlap_and_actual_start_pacing(engine, variant):
    trace = []
    p = TimedFake("paced", [0.07], trace)
    reg = Registration(p, minimum_interval_seconds=0.02)
    repo = ReviewRepository(engine, global_capacity=2, fair=True)
    job = repo.create_job(query(4), [reg])
    runner = ReviewDispatcher(repo, [reg], variant=variant, global_capacity=2)
    try:
        await drain(runner, repo, [job.id])
        assert max_overlap(trace) == 2
        assert all(
            b["start"] - a["start"] >= 0.02 for a, b in itertools.pairwise(trace)
        )
        assert runner.peak == 2
    finally:
        await runner.close()


@pytest.mark.parametrize("variant", ["A", "B"])
@pytest.mark.asyncio
async def test_zero_interval_fills_available_global_capacity(engine, variant):
    trace = []
    regs = [
        Registration(
            TimedFake(name, [0.05], trace), minimum_interval_seconds=0
        )
        for name in ("one", "two", "three")
    ]
    repo = ReviewRepository(engine, global_capacity=6, fair=True)
    job = repo.create_job(query(2), regs)
    runner = ReviewDispatcher(repo, regs, variant=variant, global_capacity=6)
    try:
        await runner.tick()
        assert len(trace) == 6 and runner.occupied() == 6
        await drain(runner, repo, [job.id])
        assert max_overlap(trace) == 6
    finally:
        await runner.close()


@pytest.mark.parametrize("variant", ["A", "B"])
@pytest.mark.asyncio
async def test_cooldown_occupies_no_execution_slot(engine, variant):
    trace = []
    providers = [
        TimedFake(p, [0.02], trace) for p in ["cooled", "ready-one", "ready-two"]
    ]
    regs = [
        Registration(p, minimum_interval_seconds=0) for p in providers
    ]
    repo = ReviewRepository(engine, global_capacity=2, fair=True)
    job = repo.create_job(query(1), regs)
    with write_session(engine) as s:
        s.add(ProviderState(provider_id="cooled", next_request_at=now_ms() + 200))
    runner = ReviewDispatcher(repo, regs, variant=variant, global_capacity=2)
    try:
        await runner.tick()
        assert {r["provider"] for r in trace} == {"ready-one", "ready-two"}
        assert set(runner.active.values()) == {"ready-one", "ready-two"}
        await drain(runner, repo, [job.id])
        assert next(r["start"] for r in trace if r["provider"] == "cooled") >= max(
            r["end"] for r in trace if r["provider"] != "cooled"
        )
    finally:
        await runner.close()


@pytest.mark.parametrize("variant", ["A", "B"])
@pytest.mark.parametrize("cache", [False, True])
@pytest.mark.asyncio
async def test_small_job_precedes_remaining_large_job(engine, variant, cache):
    trace = []
    p = TimedFake("fair", [0.02], trace)
    reg = Registration(p, minimum_interval_seconds=0)
    repo = ReviewRepository(engine, global_capacity=1, fair=True, cache_enabled=cache)
    large = repo.create_job(query(12), [reg])
    runner = ReviewDispatcher(repo, [reg], variant=variant, global_capacity=1)
    try:
        await runner.tick()
        assert len(trace) == 1
        small = repo.create_job(query(1, offset=30), [reg])
        await drain(runner, repo, [large.id, small.id])
        assert trace[1]["query"].endswith("2027-03-31")
        assert len(trace) == 13
    finally:
        await runner.close()


@pytest.mark.parametrize("variant", ["A", "B"])
@pytest.mark.asyncio
async def test_shared_fetch_and_cache_hit_never_duplicate_execution(engine, variant):
    trace = []
    p = TimedFake("shared", [0.02], trace)
    reg = Registration(p, minimum_interval_seconds=0)
    repo = ReviewRepository(engine, global_capacity=2, fair=True, cache_enabled=True)
    jobs = [repo.create_job(query(2), [reg]) for _ in range(2)]
    runner = ReviewDispatcher(repo, [reg], variant=variant, global_capacity=2)
    try:
        await drain(runner, repo, [j.id for j in jobs])
        assert len(trace) == 2
        cached = repo.create_job(query(2), [reg])
        await runner.tick()
        assert repo.get_job(cached.id)[0].status == "completed"
        assert all(
            i.attempts == 0 and i.result_origin == "cache"
            for i in repo.get_job(cached.id)[1]
        )
        assert len(trace) == 2
        with Session(engine) as s:
            assert s.scalar(select(func.count()).select_from(FareQuote)) == 12
    finally:
        await runner.close()


@pytest.mark.parametrize("cache", [False, True])
def test_global_capacity_is_atomic_across_repository_claimants(engine, cache):
    regs = [
        Registration(FakeProvider(p), minimum_interval_seconds=0)
        for p in ["one", "two", "three"]
    ]
    repo = ReviewRepository(engine, global_capacity=3, fair=True, cache_enabled=cache)
    repo.create_job(query(), regs)

    def claim(i):
        return ReviewRepository(
            engine, global_capacity=3, fair=True, cache_enabled=cache
        ).claim(regs[i % 3])

    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(claim, range(12)))
    won = [r[0] for r in results if r is not None]
    assert len(won) == 3 and len({r.id for r in won}) == 3
    assert all(
        sum(x.provider_id == reg.provider.provider_id for x in won) <= 2 for reg in regs
    )


@pytest.mark.parametrize("variant", ["A", "B"])
@pytest.mark.asyncio
async def test_timed_out_thread_retains_global_physical_capacity(engine, variant):
    release = threading.Event()

    class Late(FakeProvider):
        def __init__(self):
            super().__init__(provider_id="late")
            self.blocking = BoundedCall()
            self.key = None

        @property
        def physical_keys(self):
            return (
                {self.key}
                if self.blocking.future is not None and not self.blocking.future.done()
                else set()
            )

        async def search(self, q):
            self.key = EXECUTION_KEY.get()
            await self.blocking.run(release.wait, 2)
            return await super().search(q)

    late = Late()
    trace = []
    other = TimedFake("other", [0.01], trace)
    regs = [
        Registration(p, minimum_interval_seconds=0)
        for p in [late, other]
    ]
    repo = ReviewRepository(engine, global_capacity=1, fair=True)
    job = repo.create_job(query(1), regs)
    runner = ReviewDispatcher(repo, regs, variant=variant, global_capacity=1)
    runner.timeout_seconds = 0.03
    runner.max_attempts = 1
    try:
        await runner.tick()
        await asyncio.sleep(0.05)
        assert runner.occupied() == 1
        await runner.tick()
        assert not trace and runner.occupied() == 1
        release.set()
        await asyncio.wrap_future(late.blocking.future)
        await drain(runner, repo, [job.id])
        assert len(trace) == 1
        with Session(engine) as s:
            assert s.scalar(select(func.count()).select_from(FareQuote)) == 2
    finally:
        release.set()
        await runner.close()


@pytest.mark.parametrize("variant", ["A", "B"])
@pytest.mark.asyncio
async def test_database_failure_surfaces_instead_of_silent_worker_loss(engine, variant):
    class Broken(ReviewRepository):
        def finish(self, *args, **kwargs):
            raise RuntimeError("synthetic database failure")

    trace = []
    repo = Broken(engine, global_capacity=1, fair=True)
    reg = Registration(TimedFake("test", [0.01], trace), minimum_interval_seconds=0)
    repo.create_job(query(1), [reg])
    runner = ReviewDispatcher(repo, [reg], variant=variant, global_capacity=1)
    try:
        await runner.tick()
        await asyncio.sleep(0.03)
        with pytest.raises(RuntimeError, match="synthetic database failure"):
            await runner.tick()
    finally:
        await runner.close()
