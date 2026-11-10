"""Opt-in, bounded live benchmark; never imports into production scheduling.

Run from the repo root with .venv/bin/python scripts/benchmarks/p48_intervals.py
--run-live. Recheck published policies before each run. Only sanitized timing,
status and count metadata escapes the temporary database. No automatic retries.
Do not run alongside another client using these providers.
"""

import argparse
import asyncio
import json
import logging
import sqlite3
import tempfile
from contextlib import ExitStack
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from time import monotonic, time
from unittest.mock import patch

from alembic import command
from alembic.config import Config
from cheapwings.application.job_runner import JobRunner
from cheapwings.config import Settings
from cheapwings.domain.evidence import ProviderFailure
from cheapwings.domain.query import SearchQuery
from cheapwings.providers.registry import default_registry
from cheapwings.storage.db import database
from cheapwings.storage.repository import Repository


def utc():
    return datetime.now(UTC).isoformat(timespec="milliseconds")


def live_guard(path):
    # Read only: never claim, purge, cancel or change the owner's live queue.
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as conn:
        active = conn.execute(
            "SELECT count(*) FROM search_jobs WHERE status IN ('queued','running')"
        ).fetchone()[0]
        running = (
            conn.execute(
                "SELECT count(*) FROM provider_operations WHERE status='running'"
            ).fetchone()[0]
            + conn.execute(
                "SELECT count(*) FROM work_items WHERE status='running' AND operation_id IS NULL"
            ).fetchone()[0]
        )
        next_at = conn.execute(
            "SELECT max(next_request_at) FROM provider_state"
        ).fetchone()[0]
    return active == 0 and running == 0 and (next_at or 0) <= time() * 1000


class Measurements:
    def __init__(self, output, guard):
        self.output, self.guard = output, guard
        self.current = None
        self.rows = []
        self.octotrip_http_start = None

    def begin_http(self, kind):
        event = {"kind": kind, "start_utc": utc(), "start_monotonic": monotonic()}
        self.current["http"].append(event)
        return event

    @staticmethod
    def end_http(event, response):
        event["headers_utc"] = utc()
        event["status"] = response.status_code
        # Retry-After is policy metadata, never retain other headers or URLs.
        event["retry_after"] = response.headers.get("Retry-After")

    def emit(self, row):
        self.rows.append(row)
        line = json.dumps(row, sort_keys=True)
        with self.output.open("a") as stream:
            stream.write(line + "\n")
        print(line, flush=True)


class ObservedProvider:
    def __init__(self, provider, metrics):
        self.actual, self.metrics = provider, metrics
        self.provider_id, self.capabilities = (
            provider.provider_id,
            provider.capabilities,
        )
        self.ready = None
        self.interval = None
        self.previous_start = self.previous_finish = None

    async def search(self, query):
        if not live_guard(self.metrics.guard):
            raise ProviderFailure("benchmark_external_work_detected")
        start = monotonic()
        row = {
            "provider": self.provider_id,
            "interval": self.interval,
            "route": f"{query.origin}-{query.destination}",
            "date": str(query.departure_date),
            "start_utc": utc(),
            "start_monotonic": start,
            "ready_wait_s": start - self.ready,
            "start_gap_s": None
            if self.previous_start is None
            else start - self.previous_start,
            "post_completion_wait_s": None
            if self.previous_finish is None
            else start - self.previous_finish,
            "http": [],
            "offers": None,
            "error": None,
            "retry_after_s": 0,
        }
        self.metrics.current = row
        try:
            result = await self.actual.search(query)
            row["offers"] = sum(map(len, result.offers_by_itinerary_index))
            row["unpriced"] = result.unpriced_candidate_count
            row["status"] = result.status.value
            return result
        except BaseException as exc:
            row["error"] = (
                exc.code if isinstance(exc, ProviderFailure) else type(exc).__name__
            )
            row["retry_after_s"] = getattr(exc, "retry_after_seconds", 0)
            raise
        finally:
            finish = monotonic()
            row.update(finish_utc=utc(), latency_s=finish - start)
            self.previous_start, self.previous_finish = start, finish
            self.metrics.emit(row)
            self.metrics.current = None


def observers(stack, metrics):
    import httpx
    import httpx2
    from swoop import rpc

    # Observe send boundaries without reading bodies or changing client behavior.
    for module in (httpx, httpx2):
        original = module.AsyncClient.send

        def make_send(send):
            async def observed(client, request, **kwargs):
                # Published OctoTrip quota counts setup messages too. Keep this
                # benchmark-only guard even when testing a smaller search interval.
                policy_wait = 0
                if metrics.current["provider"] == "octotrip":
                    if metrics.octotrip_http_start is not None:
                        policy_wait = max(
                            0, 1.05 - (monotonic() - metrics.octotrip_http_start)
                        )
                        await asyncio.sleep(policy_wait)
                    metrics.octotrip_http_start = monotonic()
                event = metrics.begin_http(request.method)
                event["benchmark_policy_wait_s"] = policy_wait
                try:
                    method = json.loads(request.content).get("method")
                    if method in (
                        "initialize",
                        "notifications/initialized",
                        "tools/call",
                    ):
                        event["rpc_method"] = method
                except (ValueError, AttributeError):
                    pass
                try:
                    response = await send(client, request, **kwargs)
                    metrics.end_http(event, response)
                    return response
                finally:
                    event["send_return_utc"] = utc()

            return observed

        stack.enter_context(
            patch.object(module.AsyncClient, "send", make_send(original))
        )

    original_client = rpc._get_client

    class ClientObserver:
        def __init__(self, client):
            self.client = client

        def post(self, *args, **kwargs):
            event = metrics.begin_http("POST")
            try:
                response = self.client.post(*args, **kwargs)
                metrics.end_http(event, response)
                return response
            finally:
                event["send_return_utc"] = utc()

        def __getattr__(self, name):
            return getattr(self.client, name)

    stack.enter_context(
        patch.object(
            rpc,
            "_get_client",
            lambda *a, **kw: ClientObserver(original_client(*a, **kw)),
        )
    )


async def run(args):
    output = Path(args.output)
    if output.exists():
        raise SystemExit("Output already exists; refusing accidental repeat/append")
    metrics = Measurements(output, Path(args.live_db).resolve())
    completed = []
    if args.resume_metrics:
        completed = [
            json.loads(line)
            for line in Path(args.resume_metrics).read_text().splitlines()
        ]
    for _ in range(600):
        if live_guard(metrics.guard):
            break
        await asyncio.sleep(1)
    else:
        raise SystemExit("Live queue did not become idle; no benchmark calls sent")
    print(json.dumps({"event": "idle_preflight", "utc": utc()}), flush=True)
    settings = Settings(enabled_providers=("skiplagged", "swoop", "octotrip"))
    registrations = default_registry(settings)
    with (
        tempfile.TemporaryDirectory(prefix="cheapwings-p48-") as directory,
        ExitStack() as stack,
    ):
        url = f"sqlite:///{directory}/benchmark.db"
        cfg = Config("backend/alembic.ini")
        cfg.attributes["database_url"] = url
        command.upgrade(cfg, "head")
        logging.disable(
            logging.CRITICAL
        )  # MCP/HTTP error text can include source secrets
        observers(stack, metrics)
        engine = database(url)
        try:
            repo = Repository(engine, cache_enabled=False)
            for base in registrations:
                if base.provider.provider_id not in args.providers:
                    continue
                prior = [
                    r for r in completed if r["provider"] == base.provider.provider_id
                ]
                if any(
                    r["error"]
                    or any(h.get("status") in (401, 403, 429) for h in r["http"])
                    for r in prior
                ):
                    raise SystemExit(
                        "Refusing to resume a provider that previously failed"
                    )
                if base.unavailable_reason:
                    print(
                        json.dumps(
                            {
                                "provider": base.provider.provider_id,
                                "skipped": base.unavailable_reason,
                            }
                        )
                    )
                    continue
                observed = ObservedProvider(base.provider, metrics)
                try:
                    for interval in args.intervals:
                        stage = {10: 1, 5: 2, 2: 3, 1: 4}[interval]
                        already = sum(r["interval"] == interval for r in prior)
                        if already >= 3:
                            continue
                        if not live_guard(metrics.guard):
                            raise SystemExit(
                                "External live work detected; benchmark stopped"
                            )
                        observed.interval = interval
                        reg = replace(
                            base, provider=observed, minimum_interval_seconds=interval
                        )
                        first = date(2026, 12, 12) + timedelta(days=stage * 3 + already)
                        q = SearchQuery(
                            origins=["MEL"],
                            destinations=["DPS"],
                            departure_date_from=first,
                            departure_date_through=date(2026, 12, 12)
                            + timedelta(days=stage * 3 + 2),
                            display_currency="USD",
                            include_basic_economy=True,
                            include_hidden_city=False,
                        )
                        job = repo.create_job(q, [reg], reprice_budget=0)
                        observed.ready = monotonic()
                        runner = JobRunner(repo, [reg], max_attempts=1)
                        before = len(metrics.rows)
                        try:
                            while repo.get_job(job.id)[0].status in (
                                "queued",
                                "running",
                            ):
                                if not live_guard(metrics.guard):
                                    raise SystemExit(
                                        "External live work detected; benchmark stopped"
                                    )
                                await runner.tick()
                                await asyncio.sleep(0.1)
                                if any(
                                    r["error"]
                                    or any(
                                        h.get("status") in (401, 403, 429)
                                        for h in r["http"]
                                    )
                                    for r in metrics.rows[before:]
                                ):
                                    repo.cancel(job.id)
                                    break
                            await asyncio.gather(*runner.tasks)
                        finally:
                            await runner.close()
                        rows = metrics.rows[before:]
                        if len(rows) != 3 - already or any(
                            r["error"]
                            or any(
                                h.get("status") in (401, 403, 429) for h in r["http"]
                            )
                            for r in rows
                        ):
                            # No retry or later tier for this provider, even after cooldown.
                            break
                        if repo.get_job(job.id)[0].status != "completed":
                            break
                finally:
                    blocking = getattr(base.provider, "blocking", None)
                    if blocking:
                        blocking.close()
        finally:
            engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-live", action="store_true")
    parser.add_argument("--live-db", default="data/webtest-live.db")
    parser.add_argument("--output", default="/tmp/cheapwings-p48-metrics.jsonl")
    parser.add_argument(
        "--intervals", nargs="+", type=int, choices=(10, 5, 2, 1), default=[10, 5]
    )
    parser.add_argument(
        "--providers",
        nargs="+",
        choices=("skiplagged", "swoop", "octotrip"),
        default=["skiplagged", "swoop", "octotrip"],
    )
    parser.add_argument(
        "--resume-metrics",
        help="Skip completed samples from an earlier sanitized metadata file",
    )
    options = parser.parse_args()
    if not options.run_live:
        parser.error("Requires --run-live after reviewing provider restrictions")
    asyncio.run(run(options))
