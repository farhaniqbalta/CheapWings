"""Dedicated queue owner: python -m cheapwings.worker (POSIX local deployment)."""

import asyncio
import fcntl
import logging
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy.engine import make_url

from cheapwings.application.job_runner import JobRunner
from cheapwings.config import Settings
from cheapwings.providers.registry import default_registry
from cheapwings.storage.db import database, require_current_schema
from cheapwings.storage.repository import Repository


@contextmanager
def worker_lock(database_url):
    path = Path(make_url(database_url).database).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(path) + ".worker.lock", "a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("Another worker already owns this database") from exc
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def main():
    logging.basicConfig(level=logging.INFO)
    settings = Settings.from_env()
    with worker_lock(settings.database_url):
        engine = database(settings.database_url)
        try:
            require_current_schema(engine)
            runner = JobRunner(
                Repository(engine),
                default_registry(),
                timeout_seconds=settings.call_timeout_seconds,
                lease_seconds=settings.lease_seconds,
                max_attempts=settings.max_attempts,
            )
            asyncio.run(runner.run())
        finally:
            engine.dispose()


if __name__ == "__main__":
    main()
