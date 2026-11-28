"""P7.4: creating Discover jobs (discover work items per origin × day, Search untouched)."""

from dataclasses import replace
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import select
from sqlalchemy.orm import Session

from cheapwings.domain.query import DiscoverQuery
from cheapwings.providers.fake import FakeProvider
from cheapwings.providers.registry import Registration
from cheapwings.storage.db import database
from cheapwings.storage.models import WorkItem
from cheapwings.storage.repository import CapacityExceeded, Repository


@pytest.fixture
def engine(tmp_path):
    url = f"sqlite:///{tmp_path}/test.db"
    cfg = Config(str(Path(__file__).parents[2] / "alembic.ini"))
    cfg.attributes["database_url"] = url
    command.upgrade(cfg, "head")
    engine = database(url)
    yield engine
    engine.dispose()


def discoverer(provider_id="disc"):
    fake = FakeProvider(provider_id=provider_id)
    fake.capabilities = replace(fake.capabilities, destination_discovery=True)
    return Registration(fake, minimum_interval_seconds=0)


def query(**kw):
    return DiscoverQuery(**{"origins": [" cgk"], "departure_date_from": "2027-03-01",
                            "departure_date_through": "2027-03-07", "display_currency": "IDR", **kw})


def test_query_validates_through_the_core():
    q = query(budget="1500000")
    assert q.origins == ["CGK"]
    assert [c["date"] for c in q.calls()][:2] == ["2027-03-01", "2027-03-02"]
    assert q.model_dump(mode="json")["include_basic_economy"] is True
    with pytest.raises(ValueError, match="too_many"):
        query(origins=["CGK", "SUB"], departure_date_through="2027-03-16")
    with pytest.raises(ValueError, match="dates_reversed"):
        query(departure_date_from="2027-03-07", departure_date_through="2027-03-01")
    with pytest.raises(ValueError, match="invalid_budget"):
        query(budget="-1")


def test_creates_one_discover_item_per_call(engine):
    repo = Repository(engine)
    checker = Registration(FakeProvider(provider_id="check"), minimum_interval_seconds=0)
    job = repo.create_discovery_job(query(), [discoverer(), checker])
    assert (job.kind, job.phase, job.status) == ("discover", "discovering", "queued")
    assert job.provider_ids == ["disc", "check"]
    with Session(engine) as s:
        items = s.scalars(select(WorkItem).where(WorkItem.job_id == job.id).order_by(WorkItem.departure_date)).all()
    assert len(items) == 7
    assert {(i.provider_id, i.work_type, i.origin, i.destination, i.status) for i in items} == {
        ("disc", "discover", "CGK", "*", "pending")
    }
    assert items[0].departure_date == "2027-03-01" and items[-1].departure_date == "2027-03-07"


def test_needs_a_discovery_provider(engine):
    with pytest.raises(ValueError, match="no_discovery_provider"):
        Repository(engine).create_discovery_job(query(), [Registration(FakeProvider())])


def test_capacity_limits_apply(engine):
    repo = Repository(engine)
    repo.create_discovery_job(query(), [discoverer()], max_active=1)
    with pytest.raises(CapacityExceeded):
        repo.create_discovery_job(query(), [discoverer()], max_active=1)
