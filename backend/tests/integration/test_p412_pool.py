"""P4.12 shared global pool: no per-provider ceiling, pacing and fairness kept."""

import itertools
import threading
import time

from test_scheduler import Recorded, drain, peak, small

from cheapwings.application.job_runner import JobRunner
from cheapwings.domain.evidence import ProviderFailure
from cheapwings.providers.fake import FakeProvider
from cheapwings.providers.registry import Registration
from cheapwings.providers.swoop import BoundedCall
from cheapwings.storage.repository import Repository


async def test_single_provider_uses_whole_pool_never_more(engine, query):
    provider = Recorded("solo", 0.1)
    reg = Registration(provider, minimum_interval_seconds=0)
    repo = Repository(engine, global_capacity=12)
    job = repo.create_job(small(query, 20), [reg])
    runner = JobRunner(repo, [reg])
    try:
        await drain(runner, repo, [job.id])
        assert peak(provider.trace) == 12  # was capped at 3 before P4.12
        assert all(i.attempts == 1 for i in repo.get_job(job.id)[1])
    finally:
        await runner.close()


async def test_released_slots_alternate_when_second_provider_gets_work(engine, query):
    starts = []

    class Logged(Recorded):
        async def search(self, q):
            starts.append(self.provider_id)
            return await super().search(q)

    a, b = Logged("a", 0.05), Logged("b", 0.05)
    regs = [Registration(p, minimum_interval_seconds=0) for p in (a, b)]
    repo = Repository(engine, global_capacity=6)
    first = repo.create_job(small(query, 24), [regs[0]])
    runner = JobRunner(repo, regs)
    try:
        await runner.tick()
        assert starts == ["a"] * 6  # idle capacity is used, no fixed share for b
        second = repo.create_job(small(query, 12, offset=30), [regs[1]])
        await drain(runner, repo, [first.id, second.id])
        after = starts[6:18]
        # a cannot keep taking released slots while b has eligible work.
        assert after.count("b") >= 5
        assert max(len(list(g)) for k, g in itertools.groupby(after) if k == "a") <= 2
        assert peak(a.trace + b.trace) <= 6
    finally:
        await runner.close()


async def test_paced_provider_overlaps_with_actual_start_gaps(engine, query):
    paced, free = Recorded("paced", 0.25), Recorded("free", 0.25)
    regs = [
        Registration(paced, minimum_interval_seconds=0.02),
        Registration(free, minimum_interval_seconds=0),
    ]
    repo = Repository(engine, global_capacity=16)
    job = repo.create_job(small(query, 6), regs)
    runner = JobRunner(repo, regs)
    try:
        await drain(runner, repo, [job.id])
        assert peak(paced.trace) > 3 and peak(free.trace) == 6
        assert peak(paced.trace + free.trace) <= 16
        # Actual adapter-entry gaps; pacing never delayed the unpaced provider.
        assert all(b["start"] - a["start"] >= 0.02 for a, b in itertools.pairwise(paced.trace))
        assert free.trace[-1]["start"] - free.trace[0]["start"] < 0.02
    finally:
        await runner.close()


async def test_cooled_provider_stops_starting_and_others_take_the_pool(engine, query):
    class Limited(FakeProvider):
        calls = 0

        async def search(self, q):
            self.calls += 1
            raise ProviderFailure("http_rate_limited", 120)

    limited, other = Limited("limited"), Recorded("other", 0.05)
    regs = [Registration(p, minimum_interval_seconds=0) for p in (limited, other)]
    repo = Repository(engine, global_capacity=8)
    cooled = repo.create_job(small(query, 4), [regs[0]])
    job = repo.create_job(small(query, 8, offset=10), [regs[1]])
    runner = JobRunner(repo, regs)
    try:
        await drain(runner, repo, [job.id])
        # Uncapped admission still honors the provider-wide Retry-After cooldown.
        assert limited.calls == 4  # the first tick admitted all 4 before any 429 landed
        await runner.tick()
        assert limited.calls == 4
        assert repo.get_job(cooled.id)[0].status == "running"
        assert peak(other.trace) >= 4
    finally:
        await runner.close()


async def test_blocking_adapter_pool_sized_to_g_uses_real_threads(engine, query):
    class Threaded(FakeProvider):
        def __init__(self):
            super().__init__("threaded")
            self.blocking = BoundedCall(8)
            self.lock = threading.Lock()
            self.active = self.peak = 0

        def block(self):
            with self.lock:
                self.active += 1
                self.peak = max(self.peak, self.active)
            time.sleep(0.05)
            with self.lock:
                self.active -= 1

        async def search(self, q):
            await self.blocking.run(self.block)
            return await super().search(q)

    provider = Threaded()
    reg = Registration(provider, minimum_interval_seconds=0)
    repo = Repository(engine, global_capacity=8)
    job = repo.create_job(small(query, 16), [reg])
    runner = JobRunner(repo, [reg])
    try:
        await drain(runner, repo, [job.id])
        assert provider.peak == 8
        # No overflow rejections: dispatch never outran the executor's real capacity.
        assert all(
            i.attempts == 1 and i.status == "succeeded_results" for i in repo.get_job(job.id)[1]
        )
    finally:
        await runner.close()


class Logged(Recorded):
    def __init__(self, pid, latency, starts):
        super().__init__(pid, latency)
        self.starts = starts

    async def search(self, q):
        self.starts.append(self.provider_id)
        return await super().search(q)


async def test_lower_priority_only_gets_slots_higher_tiers_cannot_use(engine, query):
    starts = []
    high, low = Logged("high", 0.03, starts), Logged("low", 0.03, starts)
    regs = [
        Registration(low, minimum_interval_seconds=0, priority=1),
        Registration(high, minimum_interval_seconds=0, priority=0),
    ]
    repo = Repository(engine, global_capacity=2)
    job = repo.create_job(small(query, 6), regs)
    runner = JobRunner(repo, regs)
    try:
        await drain(runner, repo, [job.id])
        assert starts == ["high"] * 6 + ["low"] * 6  # registry order does not matter
    finally:
        await runner.close()


async def test_headroom_lets_late_higher_priority_work_start_immediately(engine, query):
    starts = []
    high, low = Logged("high", 0.05, starts), Logged("low", 0.5, starts)
    regs = [
        Registration(high, minimum_interval_seconds=0, priority=0),
        Registration(low, minimum_interval_seconds=0, priority=1),
    ]
    repo = Repository(engine, global_capacity=6)
    slow = repo.create_job(small(query, 20), [regs[1]])
    runner = JobRunner(repo, regs, low_priority_headroom=2)
    try:
        await runner.tick()
        await runner.tick()
        assert starts == ["low"] * 4  # the last two slots stay free
        fast = repo.create_job(small(query, 4, offset=30), [regs[0]])
        await runner.tick()
        assert starts[4:] == ["high", "high"]  # no wait for a 0.5s low-priority call
        await drain(runner, repo, [slow.id, fast.id])
        assert peak(high.trace + low.trace) <= 6 and peak(low.trace) <= 4
    finally:
        await runner.close()


async def test_headroom_unused_without_an_available_higher_priority_source(engine, query):
    low = Recorded("low", 0.1)
    reg = Registration(low, minimum_interval_seconds=0, priority=1)
    repo = Repository(engine, global_capacity=6)
    job = repo.create_job(small(query, 12), [reg])
    runner = JobRunner(repo, [reg], low_priority_headroom=2)
    try:
        await drain(runner, repo, [job.id])
        assert peak(low.trace) == 6
    finally:
        await runner.close()


def test_priority_configuration(monkeypatch):
    from cheapwings.config import Settings
    from cheapwings.providers.registry import default_registry

    settings = Settings.from_env()
    assert settings.low_priority_headroom == 2
    monkeypatch.setenv("ENABLED_PROVIDERS", "skiplagged,octotrip")
    monkeypatch.setenv("FLI_PRIORITY", "3")
    registry = default_registry(Settings.from_env())
    try:
        assert {r.provider.provider_id: r.priority for r in registry} == {
            "skiplagged": 0,
            "swoop": 0,
            "octotrip": 1,
            "fli": 3,
        }
    finally:
        for r in registry:
            if hasattr(r.provider, "blocking"):
                r.provider.blocking.close()
    monkeypatch.setenv("LOW_PRIORITY_HEADROOM", "9")
    try:
        Settings.from_env()
    except ValueError as exc:
        assert "HEADROOM" in str(exc)
    else:
        raise AssertionError("headroom >= capacity must be rejected")
