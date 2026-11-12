"""Opt-in three-search Fli C3/1s trial through the real durable SQLite runner.

Disposable migrated DB, no cache/repricing/retries. Metadata only is printed.
--live-db is read-only admission protection against overlapping owner searches.
"""

import argparse
import asyncio
import json
import logging
import sqlite3
import tempfile
import threading
from datetime import UTC, date, datetime, timedelta
from itertools import pairwise
from pathlib import Path
from time import monotonic, time

from alembic import command
from alembic.config import Config
from cheapwings.application.job_runner import JobRunner
from cheapwings.domain.evidence import ProviderFailure
from cheapwings.domain.query import SearchQuery
from cheapwings.providers.fli import FliProvider
from cheapwings.providers.registry import Registration
from cheapwings.storage.db import database
from cheapwings.storage.models import FareQuote
from cheapwings.storage.repository import Repository
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def live_guard(path):
    with sqlite3.connect(f"file:{Path(path).resolve()}?mode=ro", uri=True) as c:
        active = c.execute(
            "select count(*) from search_jobs where status in ('queued','running')"
        ).fetchone()[0]
        deadline = c.execute(
            "select max(next_request_at) from provider_state where provider_id in ('swoop','fli')"
        ).fetchone()[0]
    if active or (deadline or 0) > time() * 1000:
        raise RuntimeError(
            "Active live searches or Google provider cooldown; trial not started"
        )


async def trial(args):
    live_guard(args.live_db)
    with tempfile.TemporaryDirectory(prefix="cheapwings-p411-") as tmp:
        url = "sqlite:///" + str(Path(tmp) / "trial.db")
        cfg = Config("backend/alembic.ini")
        cfg.set_main_option("sqlalchemy.url", url)
        command.upgrade(cfg, "head")
        engine = database(url)
        repo = Repository(engine, global_capacity=args.capacity, cache_enabled=False)
        # Production sizes Fli's thread pool to G (P4.12); keep the trial identical.
        provider = FliProvider(concurrency=args.capacity)
        reg = Registration(
            provider, minimum_interval_seconds=args.interval, live_data=True
        )
        q = SearchQuery(
            origins=["HND"],
            destinations=["CGK"],
            departure_date_from=args.date,
            departure_date_through=args.date + timedelta(days=args.days - 1),
            display_currency="IDR",
        )
        job = repo.create_job(q, [reg])
        runner = JobRunner(
            repo, [reg], max_in_flight=args.capacity, max_attempts=args.max_attempts
        )
        rows, state = [], {"active": 0, "peak": 0, "blocked": False}
        lock = threading.Lock()
        actual = provider._fetch

        def fetch(request):
            row = {
                "date": str(request.departure_date),
                "start": monotonic(),
                "start_utc": datetime.now(UTC).isoformat(),
                "error": None,
            }
            with lock:
                rows.append(row)
                state["active"] += 1
                state["peak"] = max(state["peak"], state["active"])
            try:
                return actual(request)
            except ProviderFailure as error:
                row["error"] = error.code
                row["transport_code"] = getattr(error, "transport_code", None)
                if error.code in ("http_rate_limited", "auth_denied"):
                    state["blocked"] = True
                raise
            finally:
                row["end"] = monotonic()
                with lock:
                    state["active"] -= 1

        provider._fetch = fetch
        started = monotonic()
        first = None
        try:
            while monotonic() - started < 100:
                if state["blocked"]:
                    repo.cancel(job.id)
                await runner.tick()
                with Session(engine) as session:
                    count = session.scalar(select(func.count()).select_from(FareQuote))
                if count and first is None:
                    first = monotonic() - started
                status, items = repo.get_job(job.id)
                if status.status not in ("queued", "running") and not runner.tasks:
                    break
                await asyncio.sleep(0.01)
            else:
                raise RuntimeError("Trial deadline exceeded")
            duration = monotonic() - started
            ordered = sorted(rows, key=lambda r: r["start"])
            successful = sum(
                i.status in ("succeeded_results", "succeeded_empty") for i in items
            )
            print(
                json.dumps(
                    {
                        "status": status.status,
                        "blocked": state["blocked"],
                        "interval_seconds": args.interval,
                        "global_capacity": args.capacity,
                        "max_attempts": args.max_attempts,
                        "requests": len(rows),
                        "peak_in_flight": state["peak"],
                        "successful": successful,
                        "batch_seconds": round(duration, 3),
                        "successful_searches_per_minute": round(
                            successful * 60 / duration, 3
                        ),
                        "first_persisted_result_seconds": round(first, 3)
                        if first
                        else None,
                        "offers": count,
                        "actual_start_gaps_seconds": [
                            round(b["start"] - a["start"], 4)
                            for a, b in pairwise(ordered)
                        ],
                        "calls": [
                            {
                                "date": r["date"],
                                "start_utc": r["start_utc"],
                                "seconds": round(r["end"] - r["start"], 3),
                                "error": r["error"],
                                "transport_code": r.get("transport_code"),
                            }
                            for r in ordered
                        ],
                    }
                ),
                flush=True,
            )
        finally:
            await runner.close()
            engine.dispose()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-live", action="store_true")
    p.add_argument("--max-attempts", type=int, choices=(1, 3), default=1)
    p.add_argument("--live-db", required=True)
    p.add_argument("--date", type=date.fromisoformat, default=date(2026, 11, 20))
    p.add_argument("--days", type=int, default=3, help="consecutive dates = searches")
    p.add_argument("--interval", type=float, default=1.0, help="Fli start interval s")
    p.add_argument("--capacity", type=int, default=9, help="global in-flight budget")
    args = p.parse_args()
    if not args.run_live:
        p.error("Real searches require --run-live")
    logging.basicConfig(level=logging.ERROR)
    asyncio.run(trial(args))


if __name__ == "__main__":
    main()
