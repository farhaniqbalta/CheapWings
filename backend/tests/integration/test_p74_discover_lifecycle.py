"""P7.4: Discover through the durable web job runner — discovering → checking in one transaction."""

import asyncio
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from cheapwings.application.job_runner import JobRunner
from cheapwings.domain.evidence import ProviderFailure
from cheapwings.domain.query import DiscoverQuery, SearchQuery
from cheapwings.providers.fake import FakeProvider
from cheapwings.providers.registry import Registration
from cheapwings.storage.db import database, write_session
from cheapwings.storage.models import DiscoveryObservationRow, SearchJob, WorkItem
from cheapwings.storage.repository import Repository


@pytest.fixture
def engine(tmp_path):
    url = f"sqlite:///{tmp_path}/test.db"
    cfg = Config(str(Path(__file__).parents[2] / "alembic.ini"))
    cfg.attributes["database_url"] = url
    command.upgrade(cfg, "head")
    engine = database(url)
    yield engine
    engine.dispose()


def discoverer(**kw):
    fake = FakeProvider(provider_id="disc", **kw)
    # Like Skiplagged: discovers and also checks (a discovery-only source is "unavailable" in the registry).
    fake.capabilities = replace(fake.capabilities, destination_discovery=True)
    return Registration(fake, minimum_interval_seconds=0)


def checker():
    return Registration(FakeProvider(provider_id="check"), minimum_interval_seconds=0)


QUERY = DiscoverQuery(origins=["CGK"], departure_date_from="2027-03-01", departure_date_through="2027-03-02",
                      display_currency="IDR")


async def drain(runner, repo, job_id):
    for _ in range(3000):
        await runner.tick()
        if repo.get_job(job_id)[0].status not in ("queued", "running") and not runner.tasks:
            return
        await asyncio.sleep(0.002)
    raise AssertionError("worker did not drain")


def items(engine, job_id, work_type):
    with Session(engine) as s:
        return s.scalars(
            select(WorkItem).where(WorkItem.job_id == job_id, WorkItem.work_type == work_type)
            .order_by(WorkItem.provider_id, WorkItem.destination, WorkItem.departure_date)
        ).all()


def observation_count(engine, job_id):
    with Session(engine) as s:
        return s.scalar(select(func.count()).where(DiscoveryObservationRow.job_id == job_id))


async def test_discover_then_check_e2e(engine):
    repo = Repository(engine)
    disc = discoverer()  # synthetic leads: DPS 40 USD, SIN 50 USD on each day
    regs = [disc, checker()]
    job = repo.create_discovery_job(QUERY, regs)
    await drain(JobRunner(repo, regs), repo, job.id)
    job, _ = repo.get_job(job.id)
    assert (job.status, job.phase) == ("completed", "done")
    assert [i.status for i in items(engine, job.id, "discover")] == ["succeeded_results"] * 2
    detailed = items(engine, job.id, "detailed")
    # Cheapest per destination: DPS and SIN on 2027-03-01 (ties → earlier date), by both checkers.
    assert [(i.provider_id, i.destination, i.departure_date) for i in detailed] == [
        ("check", "DPS", "2027-03-01"), ("check", "SIN", "2027-03-01"),
        ("disc", "DPS", "2027-03-01"), ("disc", "SIN", "2027-03-01")]
    assert observation_count(engine, job.id) == 4
    d = job.discovery_json
    assert (d["calls_planned"], d["calls_failed"], d["unpriced"], d["outcome"]) == (2, 0, 0, "planned")
    assert (d["counts"]["selected"], d["counts"]["superseded"]) == (2, 2)


async def test_finalize_plans_once(engine):
    repo = Repository(engine)
    regs = [discoverer(), checker()]
    job = repo.create_discovery_job(QUERY, regs)
    runner = JobRunner(repo, regs)
    for _ in range(500):
        await runner.tick()
        if repo.get_job(job.id)[0].phase != "discovering" and not runner.tasks:
            break
        await asyncio.sleep(0.002)
    before = len(items(engine, job.id, "detailed"))
    with write_session(engine) as s:
        Repository.finalize(s, s.get(SearchJob, job.id), 10**13 // 10)
    assert before == 4 and len(items(engine, job.id, "detailed")) == before


async def test_restart_between_finish_and_check(engine):
    repo = Repository(engine)
    regs = [discoverer(), checker()]
    job = repo.create_discovery_job(QUERY, regs)
    first = JobRunner(repo, regs)
    for _ in range(500):
        await first.tick()
        if repo.get_job(job.id)[0].phase != "discovering" and not first.tasks:
            break
        await asyncio.sleep(0.002)
    await first.close()
    await drain(JobRunner(Repository(engine), regs), repo, job.id)  # a fresh process on the same DB
    assert observation_count(engine, job.id) == 4
    assert len(items(engine, job.id, "detailed")) == 4
    assert repo.get_job(job.id)[0].status == "completed"


async def test_discovery_all_failed_is_unavailable(engine):
    repo = Repository(engine)
    disc = discoverer()
    for day in ("2027-03-01", "2027-03-02"):
        disc.provider.script_discovery("CGK", day, ProviderFailure("schema_changed"))
    regs = [disc, checker()]
    job = repo.create_discovery_job(QUERY, regs)
    await drain(JobRunner(repo, regs), repo, job.id)
    job, _ = repo.get_job(job.id)
    assert job.status == "failed"
    assert job.discovery_json["outcome"] == "unavailable"
    assert items(engine, job.id, "detailed") == []


async def test_partial_discovery_plans(engine):
    repo = Repository(engine)
    disc = discoverer()
    disc.provider.script_discovery("CGK", "2027-03-01", ProviderFailure("schema_changed"))
    regs = [disc, checker()]
    job = repo.create_discovery_job(QUERY, regs)
    await drain(JobRunner(repo, regs), repo, job.id)
    job, _ = repo.get_job(job.id)
    assert job.status == "partial"  # one discovery call failed; every check succeeded
    assert job.discovery_json["calls_failed"] == 1
    assert {i.departure_date for i in items(engine, job.id, "detailed")} == {"2027-03-02"}


async def test_no_priced_leads_is_no_prices(engine):
    repo = Repository(engine)
    disc = discoverer(discovery_destinations=())
    regs = [disc, checker()]
    job = repo.create_discovery_job(QUERY, regs)
    await drain(JobRunner(repo, regs), repo, job.id)
    job, _ = repo.get_job(job.id)
    assert job.status == "completed" and job.discovery_json["outcome"] == "no_prices"


async def test_over_budget_is_none_under_budget(engine):
    repo = Repository(engine)
    regs = [discoverer(), checker()]
    job = repo.create_discovery_job(QUERY.model_copy(update={"budget": Decimal("100000")}), regs)
    await drain(JobRunner(repo, regs), repo, job.id)
    job, _ = repo.get_job(job.id)
    assert job.discovery_json["outcome"] == "none_under_budget"
    assert items(engine, job.id, "detailed") == []


async def test_discover_429_retries_then_succeeds(engine):
    repo = Repository(engine)
    disc = discoverer()
    calls = {"n": 0}
    original = disc.provider.discover

    async def flaky(request):
        calls["n"] += 1
        if calls["n"] == 1:
            raise ProviderFailure("http_rate_limited", 0.01)
        return await original(request)

    disc.provider.discover = flaky
    regs = [disc, checker()]
    job = repo.create_discovery_job(QUERY, regs)
    await drain(JobRunner(repo, regs), repo, job.id)
    assert repo.get_job(job.id)[0].status == "completed"
    assert calls["n"] == 3  # one rate-limited attempt, then both calls


async def test_cancel_during_discovery(engine):
    repo = Repository(engine)
    regs = [discoverer(), checker()]
    job = repo.create_discovery_job(QUERY, regs)
    repo.cancel(job.id)
    job, _ = repo.get_job(job.id)
    assert job.status == "cancelled"
    assert items(engine, job.id, "detailed") == []
    assert job.discovery_json is None


async def test_search_jobs_unchanged(engine):
    repo = Repository(engine)
    reg = Registration(FakeProvider(), minimum_interval_seconds=0)
    query = SearchQuery(origins=["CGK"], destinations=["DPS"], departure_date_from="2027-03-01",
                        departure_date_through="2027-03-02", display_currency="IDR")
    job = repo.create_job(query, [reg])
    await drain(JobRunner(repo, [reg]), repo, job.id)
    job, work = repo.get_job(job.id)
    assert (job.kind, job.status, job.discovery_json) == ("search", "completed", None)
    assert {w.work_type for w in work} == {"detailed"}


# --- final-review fixes: a source that stops us, and the deadline while discovering ---


async def test_long_retry_after_stops_source_and_plans_from_arrivals(engine):
    repo = Repository(engine)
    disc = discoverer()
    disc.provider.script_discovery("CGK", "2027-03-02", ProviderFailure("http_rate_limited", 3600))
    regs = [disc, checker()]
    job = repo.create_discovery_job(QUERY, regs)
    await drain(JobRunner(repo, regs), repo, job.id)  # must not wait out the 3600 s or the job budget
    job, _ = repo.get_job(job.id)
    d = job.discovery_json
    assert (d["calls_failed"], d["outcome"], d["stopped_providers"]) == (1, "planned", ["disc"])
    detailed = items(engine, job.id, "detailed")
    assert {(i.provider_id, i.departure_date) for i in detailed} == {("check", "2027-03-01")}
    assert job.status == "partial"


async def test_auth_denied_stops_source(engine):
    repo = Repository(engine)
    disc = discoverer()
    calls = []
    original = disc.provider.discover

    async def refused(request):
        calls.append(request.departure_date.isoformat())
        if request.departure_date.isoformat() == "2027-03-01":
            raise ProviderFailure("auth_denied")
        return await original(request)

    disc.provider.discover = refused
    disc = replace(disc, minimum_interval_seconds=0.05)  # paced like a real source: one call starts at a time
    regs = [disc, checker()]
    job = repo.create_discovery_job(QUERY, regs)
    await drain(JobRunner(repo, regs), repo, job.id)
    job, _ = repo.get_job(job.id)
    assert calls == ["2027-03-01"], "no further calls to a source that refused us"
    assert (job.status, job.discovery_json["outcome"]) == ("failed", "unavailable")
    assert items(engine, job.id, "detailed") == []


async def test_deadline_while_discovering_records_outcome(engine):
    from cheapwings.providers.base import DiscoveryRequest

    repo = Repository(engine)
    disc = discoverer()
    job = repo.create_discovery_job(QUERY, [disc, checker()])
    item, _ = repo.claim(disc)
    result = await disc.provider.discover(
        DiscoveryRequest(item.origin, __import__("datetime").date.fromisoformat(item.departure_date), "IDR"))
    assert repo.finish(item.id, item.lease_token, result)
    repo.sweep(now=job.deadline_at + 1)  # the second call never ran before the budget ended
    job, _ = repo.get_job(job.id)
    assert job.status == "partial"
    assert job.discovery_json["outcome"] == "timed_out"
    assert job.discovery_json["calls_failed"] == 1
    assert items(engine, job.id, "detailed") == []


async def test_deadline_with_nothing_found_is_unavailable(engine):
    repo = Repository(engine)
    job = repo.create_discovery_job(QUERY, [discoverer(), checker()])
    repo.sweep(now=job.deadline_at + 1)
    job, _ = repo.get_job(job.id)
    assert (job.status, job.discovery_json["outcome"]) == ("failed", "unavailable")
