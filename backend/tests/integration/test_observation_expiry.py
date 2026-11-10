import asyncio
from datetime import timedelta

from cheapwings.application.job_runner import JobRunner
from cheapwings.application.search_service import results_projection
from cheapwings.providers.fake import FakeProvider
from cheapwings.providers.registry import Registration
from cheapwings.storage.repository import Repository, now_ms


async def test_short_source_expiry_preserves_other_source_and_running_job(engine, query, monkeypatch):
    clock = [now_ms()]
    monkeypatch.setattr('cheapwings.storage.repository.now_ms', lambda: clock[0])
    monkeypatch.setattr('cheapwings.application.search_service.now_ms', lambda: clock[0])
    # purge imports repository.now_ms, so both storage and projection share this clock.
    regs = [Registration(FakeProvider(provider_id=name), minimum_interval_seconds=0,
                         retention_seconds=seconds)
            for name, seconds in [('short', 900), ('long', 3600)]]
    q = query.model_copy(update={'destinations': ['DPS'], 'departure_date_through': query.departure_date_from + timedelta(days=1)})
    repo = Repository(engine)
    job = repo.create_job(q, regs, budget_seconds=1800)
    runner = JobRunner(repo, regs)
    try:
        await runner.tick()
        await asyncio.gather(*runner.tasks)
        before = results_projection(repo, job.id, 'lowest_advertised')
        assert before.itineraries
        original_deadline = repo.get_job(job.id)[0].deadline_at
        clock[0] += 901_000
        expired = results_projection(repo, job.id, 'lowest_advertised')
        assert expired.status == 'running'
        assert {x.provider_id for x in expired.expired_observations} == {'short'}
        assert {offer.provider_id for row in expired.itineraries for offer in row.offers} == {'long'}
        assert repo.get_job(job.id)[0].deadline_at == original_deadline
        await runner.tick()
        await asyncio.gather(*runner.tasks)
        after = results_projection(repo, job.id, 'lowest_advertised')
        assert after.status == 'completed'
        assert {offer.provider_id for row in after.itineraries for offer in row.offers} == {'short', 'long'}
        # Results and metadata survive reopening the repository; no price resurrection.
        clock[0] += 3_601_000
        restored = results_projection(Repository(engine), job.id, 'best_checked')
        assert restored.itineraries == []
        assert len(restored.expired_observations) == 4
        assert all(item.observed_at and item.expired_at for item in restored.expired_observations)
        assert 'amount' not in restored.expired_observations[0].model_dump()
    finally:
        await runner.close()


def test_rest_budget_is_not_minimum_source_retention(engine):
    from test_api import client_for, request_data
    regs = [Registration(FakeProvider(provider_id=name), live_data=True, retention_seconds=ttl)
            for name, ttl in [('short', 900), ('long', 3600)]]
    with client_for(engine, regs) as client:
        response = client.post('/api/v1/searches', json=request_data())
        assert response.status_code == 202
        job = client.app.state.repository.get_job(response.json()['job_id'])[0]
        assert job.deadline_at - job.created_at == 1800_000
        assert job.data_expires_at is None


async def test_legacy_migration_keeps_quotes_and_original_cutoff(tmp_path, query):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import select, func
    from sqlalchemy.orm import Session
    from cheapwings.storage.db import database
    from cheapwings.storage.models import WorkItem, FareQuote
    from test_worker import single, drain
    config = Config('backend/alembic.ini')
    config.attributes['database_url'] = 'sqlite:///' + str(tmp_path / 'migration.db')
    command.upgrade(config, 'head')
    engine = database(config.attributes['database_url'])
    repo = Repository(engine)
    reg = Registration(FakeProvider(), minimum_interval_seconds=0)
    job = repo.create_job(single(query), [reg], retention_seconds=60)
    await drain(JobRunner(repo, [reg]), repo, job.id)
    with Session(engine) as s:
        before = s.scalar(select(func.count()).select_from(FareQuote))
    command.downgrade(config, '8d103ce214ab')
    command.upgrade(config, 'head')
    command.upgrade(config, 'head')
    command.check(config)
    with Session(engine) as s:
        assert s.scalar(select(func.count()).select_from(FareQuote)) == before > 0
        assert {x.data_expires_at for x in s.scalars(select(WorkItem))} == {job.data_expires_at}
    engine.dispose()
