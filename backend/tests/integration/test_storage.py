from datetime import timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from cheapwings.domain.query import SearchQuery
from cheapwings.providers.fake import FakeProvider
from cheapwings.providers.registry import Registration
from cheapwings.storage.db import database, write_session
from cheapwings.storage.models import WorkItem
from cheapwings.storage.repository import Repository


def migrate(url, direction="up"):
    config = Config(str(Path(__file__).parents[2] / "alembic.ini"))
    config.attributes["database_url"] = url
    if direction == "up":
        command.upgrade(config, "head")
    else:
        command.downgrade(config, "base")


@pytest.fixture
def engine(tmp_path):
    url = f"sqlite:///{tmp_path}/test.db"
    migrate(url)
    engine = database(url)
    yield engine
    engine.dispose()


@pytest.fixture
def query():
    return SearchQuery(
        origins=["MEL"],
        destinations=["CGK", "DPS", "SUB"],
        departure_date_from="2026-12-12",
        departure_date_through="2026-12-20",
        display_currency="IDR",
    )


def test_migrations_constraints_and_snapshot(engine, query):
    registry = [
        Registration(FakeProvider()),
        Registration(FakeProvider(provider_id="off"), enabled=False, disabled_reason="test"),
    ]
    repo = Repository(engine)
    job = repo.create_job(query, registry)
    query.origins.append("SYD")
    saved, items = repo.get_job(job.id)
    assert saved.query_json["origins"] == ["MEL"]
    assert len(items) == 54
    assert sum(i.status == "skipped_unsupported" for i in items) == 27
    with engine.connect() as c:
        assert c.exec_driver_sql("PRAGMA journal_mode").scalar() == "wal"
        assert c.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
        assert c.exec_driver_sql("PRAGMA busy_timeout").scalar() == 5000
    with pytest.raises(IntegrityError), write_session(engine) as s:
        item = items[0]
        s.add(
            WorkItem(
                id="duplicate",
                job_id=job.id,
                provider_id=item.provider_id,
                origin=item.origin,
                destination=item.destination,
                departure_date=item.departure_date,
                status="pending",
            )
        )
    with pytest.raises(IntegrityError), write_session(engine) as s:
        s.add(
            WorkItem(
                id="orphan",
                job_id="missing",
                provider_id="x",
                origin="MEL",
                destination="DPS",
                departure_date="2026-12-12",
                status="pending",
            )
        )
    with Session(engine) as s:
        assert len(s.scalars(select(WorkItem)).all()) == 54
    url = str(engine.url)
    migrate(url, "down")
    assert inspect(engine).get_table_names() == ["alembic_version"]
    migrate(url)
    assert "fare_quotes" in inspect(engine).get_table_names()


def test_configured_query_cap_survives_snapshot(engine, query):
    from cheapwings.application.search_service import status_projection
    from cheapwings.providers.registry import Registration

    q = query.model_copy(
        update={
            "max_combinations": 240,
            "departure_date_through": query.departure_date_from + timedelta(days=45),
        }
    )
    q = SearchQuery.model_validate(q.model_dump() | {"max_combinations": 240})
    repo = Repository(engine)
    reg = Registration(FakeProvider(), minimum_interval_seconds=0)
    job = repo.create_job(q, [reg])
    item, restored = repo.claim(reg)
    assert restored.max_combinations == 240
    assert item is not None
    assert status_projection(repo, job.id).total_route_date_combinations == len(
        repo.get_job(job.id)[1]
    )
