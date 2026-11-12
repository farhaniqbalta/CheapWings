"""Offline overlapping failure experiments; no provider/network traffic."""
# Imported pytest fixtures intentionally retain their names.
# ruff: noqa: F811

import asyncio
import json
import sqlite3
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "backend/tests/integration")
)
import cheapwings.storage.repository as repository_module
from cheapwings.application.job_runner import JobRunner
from cheapwings.domain.evidence import ProviderFailure
from cheapwings.providers.base import SingleDateRouteQuery
from cheapwings.providers.fake import FakeProvider
from cheapwings.providers.registry import Registration
from cheapwings.providers.swoop import BoundedCall, SwoopProvider
from cheapwings.storage.models import FareQuote, ProviderState, WorkAttempt
from cheapwings.storage.repository import Repository, now_ms
from test_storage import engine, query  # noqa: F401


def record(case, **values):
    with open("/tmp/p48-failure-metrics.jsonl", "a") as stream:
        stream.write(json.dumps({"case": case, **values}) + "\n")


def short(query, n=3):
    return query.model_copy(
        update={
            "destinations": ["DPS"],
            "departure_date_through": query.departure_date_from.replace(day=11 + n),
        }
    )


async def drain(runner, repo, job):
    for _ in range(100):
        await runner.tick()
        if repo.get_job(job)[0].status not in ("queued", "running"):
            await asyncio.gather(*runner.tasks)
            return
        await asyncio.sleep(0.001)
    raise AssertionError("not drained")


@pytest.mark.parametrize("cache", [False, True])
@pytest.mark.asyncio
async def test_two_overlapping_calls_cancel_and_replacement(engine, query, cache):
    release = asyncio.Event()

    class Gate(FakeProvider):
        active = 0
        maximum = 0

        async def search(self, q):
            self.active += 1
            self.maximum = max(self.maximum, self.active)
            try:
                await release.wait()
                return await super().search(q)
            finally:
                self.active -= 1

    provider = Gate()
    reg = Registration(provider, minimum_interval_seconds=0)
    repo = Repository(engine, cache_enabled=cache, global_capacity=2)
    first = repo.create_job(short(query), [reg])
    runner = JobRunner(repo, [reg])
    try:
        await runner.tick()
        assert provider.active == 2
        repo.cancel(first.id)
        second = repo.create_job(short(query), [reg])
        await runner.tick()
        assert provider.active == 2
        release.set()
        await asyncio.gather(*runner.tasks)
        await drain(runner, repo, second.id)
        with Session(engine) as s:
            assert s.scalar(select(func.count()).select_from(FareQuote)) == 6
        assert all(not (i.result_count or 0) for i in repo.get_job(first.id)[1])
        assert provider.maximum == 2
        record("cancel_overlap", cache=cache, peak=provider.maximum, committed_offers=6)
    finally:
        release.set()
        await runner.close()


@pytest.mark.parametrize("cache", [False, True])
@pytest.mark.asyncio
async def test_overlap_429_retry_after_and_independent_provider(
    engine, query, cache, monkeypatch
):
    release = asyncio.Event()

    class Limited(FakeProvider):
        calls = 0
        active = 0
        maximum = 0

        async def search(self, q):
            self.calls += 1
            number = self.calls
            self.active += 1
            self.maximum = max(self.maximum, self.active)
            try:
                await release.wait()
                if number == 1:
                    raise ProviderFailure("http_rate_limited", 120)
                return await super().search(q)
            finally:
                self.active -= 1

    p = Limited()
    reg = Registration(p, minimum_interval_seconds=0)
    other = Registration(
        FakeProvider("other"), minimum_interval_seconds=0
    )
    repo = Repository(engine, cache_enabled=cache, global_capacity=4)
    job = repo.create_job(short(query), [reg, other])
    runner = JobRunner(repo, [reg, other])
    try:
        await runner.tick()
        assert p.maximum == 2
        release.set()
        await asyncio.gather(*runner.tasks)
        with Session(engine) as s:
            until = s.get(ProviderState, "fake").next_request_at
        monkeypatch.setattr(repository_module, "now_ms", lambda: until - 1)
        await runner.tick()
        await asyncio.gather(*runner.tasks)
        assert p.calls == 2
        assert all(
            i.status.startswith("succeeded")
            for i in repo.get_job(job.id)[1]
            if i.provider_id == "other"
        )
        monkeypatch.setattr(repository_module, "now_ms", lambda: until)
        await drain(runner, repo, job.id)
        assert p.calls == 4
        with Session(engine) as s:
            assert s.scalar(select(func.count()).select_from(FareQuote)) == 12
        record(
            "overlap_429",
            cache=cache,
            peak=p.maximum,
            actual_calls=p.calls,
            committed_offers=12,
            cooldown_seconds=120,
        )
    finally:
        await runner.close()


@pytest.mark.parametrize("cache", [False, True])
@pytest.mark.asyncio
async def test_two_expired_leases_reject_late_successes(engine, query, cache):
    repo = Repository(engine, cache_enabled=cache)
    reg = Registration(FakeProvider(), minimum_interval_seconds=0)
    job = repo.create_job(short(query, 2), [reg])
    now = now_ms()
    old = [repo.claim(reg, lease_seconds=1, now=now)[0] for _ in range(2)]
    repo.sweep(now=now + 1001)
    new = [repo.claim(reg, now=now + 1001)[0] for _ in range(2)]
    for item in old:
        request = SingleDateRouteQuery(
            item.origin,
            item.destination,
            date.fromisoformat(item.departure_date),
            True,
            False,
            "IDR",
        )
        assert not repo.finish(
            item.id,
            item.lease_token,
            await reg.provider.search(request),
            now=now + 1002,
        )
    for item in new:
        request = SingleDateRouteQuery(
            item.origin,
            item.destination,
            date.fromisoformat(item.departure_date),
            True,
            False,
            "IDR",
        )
        assert repo.finish(
            item.id,
            item.lease_token,
            await reg.provider.search(request),
            now=now + 1002,
        )
    with Session(engine) as s:
        assert s.scalar(select(func.count()).select_from(FareQuote)) == 4
    assert repo.get_job(job.id)[0].status == "completed"
    record(
        "late_success_fencing", cache=cache, expired=2, reclaimed=2, committed_offers=4
    )


@pytest.mark.asyncio
async def test_timeout_keeps_two_real_blocking_slots_and_rejects_more():
    slots = [BoundedCall(), BoundedCall()]
    release = threading.Event()
    state = {"active": 0, "peak": 0}
    lock = threading.Lock()

    def stalled():
        with lock:
            state["active"] += 1
            state["peak"] = max(state["active"], state["peak"])
        try:
            release.wait(3)
            return "late"
        finally:
            with lock:
                state["active"] -= 1

    tasks = [
        asyncio.create_task(asyncio.wait_for(slot.run(stalled), 0.05)) for slot in slots
    ]
    try:
        outcomes = await asyncio.gather(*tasks, return_exceptions=True)
        assert all(isinstance(e, TimeoutError) for e in outcomes)
        assert state["active"] == 2
        for slot in slots:
            with pytest.raises(ProviderFailure):
                await slot.run(stalled)
        assert state["peak"] == 2
        record(
            "stalled_threads",
            peak=state["peak"],
            await_timeouts=2,
            extra_submissions_rejected=2,
        )
    finally:
        release.set()
        for slot in slots:
            if slot.future:
                await asyncio.wrap_future(slot.future)
            slot.close()


@pytest.mark.asyncio
async def test_stock_swoop_one_instance_cannot_overlap():
    p = SwoopProvider()
    release = threading.Event()
    started = threading.Event()
    calls = []

    def invoke(*args):
        calls.append(1)
        started.set()
        release.wait(3)
        raise ProviderFailure("synthetic_transport_stop")

    p._invoke = invoke
    q = SingleDateRouteQuery("MEL", "DPS", date(2027, 1, 19), True, False, "USD")
    first = asyncio.create_task(p.search(q))
    try:
        for _ in range(100):
            if started.is_set():
                break
            await asyncio.sleep(0.001)
        assert started.is_set()
        with pytest.raises(ProviderFailure, match="provider_unavailable"):
            await p.search(q)
        assert len(calls) == 1
        record("stock_swoop_c2", logical_attempts=2, actual_invocations=1, peak=1)
    finally:
        release.set()
        await asyncio.gather(first, return_exceptions=True)
        p.blocking.close()


@pytest.mark.parametrize("cache", [False, True])
def test_concurrent_claims_under_real_sqlite_lock(engine, query, cache):
    repo = Repository(engine, cache_enabled=cache)
    reg = Registration(FakeProvider(), minimum_interval_seconds=0)
    repo.create_job(short(query), [reg])
    lock = sqlite3.connect(engine.url.database)
    lock.execute("BEGIN IMMEDIATE")

    def claim(_):
        start = time.monotonic()
        value = Repository(engine, cache_enabled=cache, global_capacity=2).claim(reg)
        return value, time.monotonic() - start

    try:
        with ThreadPoolExecutor(max_workers=16) as pool:
            futures = [pool.submit(claim, i) for i in range(16)]
            time.sleep(0.05)
            lock.rollback()
            results = [f.result() for f in futures]
        assert sum(r[0] is not None for r in results) == 2
        waits = sorted(r[1] for r in results)
        record(
            "sqlite_contention",
            cache=cache,
            racing_claimants=16,
            winners=2,
            claim_p50_s=waits[7],
            claim_p95_s=waits[-1],
            errors=0,
        )
    finally:
        lock.close()


def test_actual_worker_process_kill_and_recovery(engine, query, tmp_path, monkeypatch):
    repo = Repository(engine)
    reg = Registration(FakeProvider(), minimum_interval_seconds=0)
    job = repo.create_job(short(query, 2), [reg])
    child = tmp_path / "worker.py"
    started = tmp_path / "started.txt"
    child.write_text("""import asyncio,sys
from cheapwings.application.job_runner import JobRunner
from cheapwings.providers.fake import FakeProvider
from cheapwings.providers.registry import Registration
from cheapwings.storage.db import database
from cheapwings.storage.repository import Repository
class Slow(FakeProvider):
    async def search(self,q):
        with open(sys.argv[2],"a") as stream:
            stream.write(str(q.departure_date)+"\\n")
        await asyncio.sleep(30)
        return await super().search(q)
async def main():
    repo=Repository(database(sys.argv[1]))
    runner=JobRunner(repo,[Registration(Slow(),minimum_interval_seconds=0)])
    await runner.run()
asyncio.run(main())
""")
    proc = subprocess.Popen(
        [sys.executable, str(child), str(engine.url), str(started)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    old = []
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            old = [i for i in repo.get_job(job.id)[1] if i.status == "running"]
            if (
                len(old) == 2
                and started.exists()
                and len(started.read_text().splitlines()) == 2
            ):
                break
            time.sleep(0.01)
        assert len(old) == 2
        assert len(started.read_text().splitlines()) == 2
    finally:
        proc.kill()
        proc.wait(timeout=5)
    assert repo.claim(reg) is None
    after = max(i.leased_until for i in old) + 1
    monkeypatch.setattr(repository_module, "now_ms", lambda: after)
    repo.sweep()
    for item in old:
        assert not repo.finish(
            item.id, item.lease_token, error_code="provider_unavailable"
        )

    async def recover():
        runner = JobRunner(Repository(engine), [reg])
        try:
            await drain(runner, repo, job.id)
        finally:
            await runner.close()

    asyncio.run(recover())
    with Session(engine) as s:
        assert s.scalar(select(func.count()).select_from(FareQuote)) == 4
        assert s.scalar(select(func.count()).select_from(WorkAttempt)) == 4
    record(
        "process_crash",
        killed_pid=proc.pid,
        interrupted=2,
        retry_attempts=2,
        committed_offers=4,
        lease_expiry="simulated_clock_advance_after_real_kill",
    )
