import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from cheapwings.application.job_runner import JobRunner, ProviderFailure
from cheapwings.domain.coverage import WorkStatus
from cheapwings.domain.offer import ProviderErrorCode
from cheapwings.providers.fake import FakeProvider, ScriptedOutcome
from cheapwings.providers.registry import Registration
from cheapwings.storage.models import FareQuote, WorkAttempt, WorkItem
from cheapwings.storage.repository import Repository, now_ms


def single(query):
    return query.model_copy(
        update={"destinations": ["DPS"], "departure_date_through": query.departure_date_from}
    )


async def drain(runner, repo, job_id):
    for _ in range(500):
        await runner.tick()
        if repo.get_job(job_id)[0].status not in ("queued", "running"):
            await runner.close()
            return
        await asyncio.sleep(0.001)
    raise AssertionError("job did not finish")


async def test_worker_multi_provider_partial_and_empty(engine, query):
    repo = Repository(engine)
    p1, p2 = FakeProvider(), FakeProvider(provider_id="second")
    p2.script(
        "MEL",
        "DPS",
        query.departure_date_from,
        ScriptedOutcome(WorkStatus.FAILED_TERMINAL, ProviderErrorCode.AUTH_DENIED),
    )
    p1.script("MEL", "CGK", query.departure_date_from, ScriptedOutcome(WorkStatus.SUCCEEDED_EMPTY))
    registry = [Registration(p, minimum_interval_seconds=0) for p in (p1, p2)]
    job = repo.create_job(query, registry)
    runner = JobRunner(repo, registry)
    await drain(runner, repo, job.id)
    saved, items = repo.get_job(job.id)
    assert saved.status == "partial"
    assert len(items) == 54
    assert sum(i.status == "succeeded_empty" for i in items) == 1
    assert sum(i.status == "failed_terminal" for i in items) == 1
    with Session(engine) as s:
        assert s.scalar(select(func.count()).select_from(FareQuote)) == 104
        assert len(s.scalars(select(WorkAttempt)).all()) == 54


async def test_restart_recovery_and_fencing(engine, query):
    repo = Repository(engine)
    reg = Registration(FakeProvider(), minimum_interval_seconds=0)
    q = single(query)
    job = repo.create_job(q, [reg])
    item, _ = repo.claim(reg, lease_seconds=1)
    from cheapwings.providers.base import SingleDateRouteQuery

    result = await reg.provider.search(
        SingleDateRouteQuery("MEL", "DPS", q.departure_date_from, True, False, "IDR")
    )
    repo.sweep(now=now_ms() + 2000)
    assert not repo.finish(item.id, item.lease_token, result)
    new, _ = repo.claim(reg)
    assert new.id == item.id and new.attempts == 2
    assert repo.finish(new.id, new.lease_token, result)
    assert not repo.finish(new.id, new.lease_token, result)
    with Session(engine) as s:
        assert s.scalar(select(func.count()).select_from(FareQuote)) == 2
        attempts = s.scalars(select(WorkAttempt).order_by(WorkAttempt.attempt)).all()
        assert [a.outcome for a in attempts] == ["lease_expired", "succeeded_results"]
    assert repo.get_job(job.id)[0].status == "completed"


async def test_completed_pairs_survive_worker_recreation(engine, query):
    repo = Repository(engine)
    q = query.model_copy(
        update={
            "destinations": ["DPS"],
            "departure_date_through": query.departure_date_from.replace(day=13),
        }
    )
    reg = Registration(FakeProvider(), minimum_interval_seconds=0)
    job = repo.create_job(q, [reg])
    runner = JobRunner(repo, [reg])
    await runner.tick()
    await asyncio.gather(*runner.tasks)
    await runner.close()
    assert sum(i.status == "succeeded_results" for i in repo.get_job(job.id)[1]) == 1
    crashed, _ = repo.claim(reg)
    repo.sweep(now=now_ms() + 50_000)
    await drain(JobRunner(Repository(engine), [reg]), repo, job.id)
    assert repo.get_job(job.id)[0].status == "completed"
    assert {i.id: i.attempts for i in repo.get_job(job.id)[1]}[crashed.id] == 2
    with Session(engine) as s:
        assert s.scalar(select(func.count()).select_from(FareQuote)) == 4


async def test_cancel_fences_late_response_preserves_success(engine, query):
    repo = Repository(engine)
    reg = Registration(FakeProvider(), minimum_interval_seconds=0)
    job = repo.create_job(query, [reg])
    runner = JobRunner(repo, [reg])
    await runner.tick()
    await asyncio.gather(*runner.tasks)
    item, _ = repo.claim(reg)
    repo.cancel(job.id)
    repo.cancel(job.id)
    assert repo.claim(reg) is None
    assert not repo.finish(item.id, item.lease_token, error_code="unknown")
    assert repo.get_job(job.id)[0].status == "cancelled"
    with Session(engine) as s:
        assert s.scalar(select(func.count()).select_from(FareQuote)) == 2
    await runner.close()


def test_atomic_claim_and_global_provider_limit(engine, query):
    repo = Repository(engine)
    reg = Registration(FakeProvider(), minimum_interval_seconds=0)
    repo.create_job(query, [reg])
    repo.create_job(single(query), [reg])
    with ThreadPoolExecutor(max_workers=2) as pool:
        claims = list(pool.map(lambda _: Repository(engine).claim(reg), range(2)))
    assert sum(c is not None for c in claims) == 1


def test_retry_after_global_cooldown_and_attempt_limit(engine, query):
    repo = Repository(engine)
    reg = Registration(FakeProvider(), minimum_interval_seconds=0)
    job = repo.create_job(single(query), [reg])
    item, _ = repo.claim(reg)
    start = now_ms()
    repo.finish(
        item.id,
        item.lease_token,
        error_code="http_rate_limited",
        retry_after_seconds=120,
        now=start,
    )
    assert repo.claim(reg, now=start + 119_999) is None
    new, _ = repo.claim(reg, now=start + 120_000)
    repo.finish(
        new.id, new.lease_token, error_code="http_rate_limited", max_attempts=2, now=start + 120_001
    )
    assert repo.get_job(job.id)[0].status == "failed"


async def test_timeout_and_unexpected_error_are_not_empty(engine, query):
    repo = Repository(engine)
    provider = FakeProvider()
    provider.script(
        "MEL",
        "DPS",
        query.departure_date_from,
        ScriptedOutcome(WorkStatus.SUCCEEDED_EMPTY, delay_seconds=1),
    )
    reg = Registration(provider, minimum_interval_seconds=0)
    job = repo.create_job(single(query), [reg])
    await drain(
        JobRunner(repo, [reg], timeout_seconds=0.01, lease_seconds=1, max_attempts=1), repo, job.id
    )
    assert repo.get_job(job.id)[1][0].last_error_code == "network_timeout"
    assert repo.get_job(job.id)[0].status == "failed"


def test_global_job_budget_exhaustion(engine, query):
    repo = Repository(engine)
    job = repo.create_job(query, [Registration(FakeProvider())], budget_seconds=1)
    repo.sweep(now=now_ms() + 2000)
    assert repo.get_job(job.id)[0].status == "failed"
    assert all(i.last_error_detail == "job budget exhausted" for i in repo.get_job(job.id)[1])


async def test_offer_write_rollback_is_atomic(engine, query):
    repo = Repository(engine)
    reg = Registration(FakeProvider(), minimum_interval_seconds=0)
    repo.create_job(single(query), [reg])
    item, q = repo.claim(reg)
    from cheapwings.providers.base import SingleDateRouteQuery

    result = await reg.provider.search(
        SingleDateRouteQuery("MEL", "DPS", q.departure_date_from, True, False, "IDR")
    )
    original = repo._store_results

    def broken(*args):
        original(*args)
        raise RuntimeError("simulated crash before commit")

    repo._store_results = broken
    with pytest.raises(RuntimeError):
        repo.finish(item.id, item.lease_token, result)
    with Session(engine) as s:
        assert s.scalar(select(func.count()).select_from(FareQuote)) == 0
        assert s.get(WorkItem, item.id).status == "running"
    repo._store_results = original
    assert repo.finish(item.id, item.lease_token, result)


async def test_cancel_does_not_release_live_provider_slot(engine, query):
    class SlowProvider(FakeProvider):
        started = 0
        release = None

        async def search(self, request):
            self.started += 1
            await self.release.wait()
            return await super().search(request)

    p = SlowProvider()
    p.release = asyncio.Event()
    reg = Registration(p, minimum_interval_seconds=0)
    repo = Repository(engine)
    first = repo.create_job(single(query), [reg])
    runner = JobRunner(repo, [reg])
    await runner.tick()
    assert p.started == 1
    repo.cancel(first.id)
    second = repo.create_job(single(query), [reg])
    await runner.tick()
    assert p.started == 1
    p.release.set()
    await asyncio.gather(*runner.tasks)
    await drain(runner, repo, second.id)
    assert p.started == 2


async def test_removed_provider_explicitly_skipped(engine, query):
    repo = Repository(engine)
    job = repo.create_job(single(query), [Registration(FakeProvider())])
    runner = JobRunner(repo, [])
    await runner.tick()
    saved, items = repo.get_job(job.id)
    assert saved.status == "failed"
    assert items[0].status == "skipped_unsupported"
    assert "removed" in items[0].last_error_detail
    await runner.close()


def test_worker_exclusive_ownership_and_schema(engine):
    from cheapwings.storage.db import require_current_schema
    from cheapwings.worker import worker_lock

    require_current_schema(engine)
    with worker_lock(str(engine.url)), pytest.raises(RuntimeError), worker_lock(str(engine.url)):
        pass


async def test_rate_limit_exception_preserves_retry_after(engine, query):
    class Limited(FakeProvider):
        async def search(self, request):
            raise ProviderFailure("http_rate_limited", retry_after_seconds=90)

    repo = Repository(engine)
    reg = Registration(Limited(), minimum_interval_seconds=0)
    job = repo.create_job(single(query), [reg])
    runner = JobRunner(repo, [reg])
    start = now_ms()
    await runner.tick()
    await asyncio.gather(*runner.tasks)
    item = repo.get_job(job.id)[1][0]
    assert item.status == "retry_wait"
    assert item.next_attempt_at >= start + 90_000
    assert repo.claim(reg, now=start + 89_999) is None
    await runner.close()
