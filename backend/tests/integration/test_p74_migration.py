"""P7.4 migration: Discover jobs and observations on top of an existing durable DB."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from cheapwings.storage.db import database, require_current_schema
from cheapwings.storage.repository import Repository


def config(url):
    cfg = Config(str(Path(__file__).parents[2] / "alembic.ini"))
    cfg.attributes["database_url"] = url
    return cfg


def test_migration_keeps_search_rows(tmp_path):
    url = f"sqlite:///{tmp_path}/old.db"
    command.upgrade(config(url), "a49b10d15c01")  # the P6 head
    engine = database(url)
    with engine.begin() as c:
        c.execute(text(
            "INSERT INTO search_jobs (id, query_json, dispatch_sequence, status, phase, cancel_requested, created_at,"
            " updated_at, deadline_at, cache_mode, upstream_work_reserved, reprice_budget, reprice_providers,"
            " verification_planned) VALUES ('old', '{}', 0, 'completed', 'done', 0, 1, 1, 9, 'prefer_cache', 1, 0,"
            " '[]', 0)"
        ))
    command.upgrade(config(url), "head")
    require_current_schema(engine)
    with engine.connect() as c:
        assert c.execute(text("SELECT kind, discovery_json FROM search_jobs WHERE id='old'")).one() == ("search", None)
    assert "discovery_observations" in inspect(engine).get_table_names()
    job, items = Repository(engine).get_job("old")
    assert job.kind == "search" and job.discovery_json is None and items == []
    command.downgrade(config(url), "a49b10d15c01")
    assert "discovery_observations" not in inspect(engine).get_table_names()
    assert "kind" not in {col["name"] for col in inspect(engine).get_columns("search_jobs")}
    command.upgrade(config(url), "head")
    engine.dispose()
