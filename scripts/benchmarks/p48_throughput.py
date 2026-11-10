"""Isolated throughput experiment. No production configuration is changed.

Live: --mode live --output /tmp/p48-throughput-live.jsonl --run-live
Offline: --mode synthetic --latency 30 --output /tmp/p48-synthetic-30.jsonl
"""

import argparse
import asyncio
import heapq
import itertools
import json
import logging
import math
import random
import resource
import tempfile
import tracemalloc
from contextlib import ExitStack
from contextvars import ContextVar
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from time import monotonic
from unittest.mock import patch

from alembic import command
from alembic.config import Config
from cheapwings.application.job_runner import JobRunner
from cheapwings.domain.evidence import ProviderFailure
from cheapwings.domain.query import SearchQuery
from cheapwings.providers.fake import FakeProvider
from cheapwings.providers.octotrip import OctotripProvider
from cheapwings.providers.registry import Registration
from cheapwings.providers.skiplagged import SkiplaggedProvider
from cheapwings.providers.swoop import SwoopProvider
from cheapwings.storage.db import database
from cheapwings.storage.models import SearchJob
from cheapwings.storage.repository import Repository
from p48_intervals import live_guard
from sqlalchemy import event, func, select
from sqlalchemy.orm import Session

CURRENT = ContextVar("p48_call", default=None)


def percentile(values, p):
    return sorted(values)[max(0, math.ceil(len(values) * p) - 1)] if values else None


def emit(path, row):
    with Path(path).open("a") as stream:
        stream.write(json.dumps(row, sort_keys=True) + "\n")
    if row["kind"] != "call":
        print(json.dumps(row, sort_keys=True), flush=True)


class Experiment:
    def __init__(self, output):
        self.output = output
        self.blocked = set()
        self.rows = []
        self.octo_lock = asyncio.Lock()
        self.octo_last = None
        self.attempted = {}

    def feedback(self, row, response):
        if response.status_code in (401, 403, 429):
            self.blocked.add(row["provider"])

    async def before_http(self, row):
        if row["provider"] in self.blocked:
            raise ProviderFailure("benchmark_stopped")
        if row["provider"] == "octotrip":
            async with self.octo_lock:
                if self.octo_last is not None:
                    await asyncio.sleep(max(0, self.octo_last + 1.10 - monotonic()))
                if row["provider"] in self.blocked:
                    raise ProviderFailure("benchmark_stopped")
                self.octo_last = monotonic()

    def instrument(self, stack):
        import httpx
        import httpx2
        import swoop
        from swoop import rpc

        actual_search = swoop.search

        def sdk_search(*args, **kwargs):
            try:
                return actual_search(*args, **kwargs)
            except Exception as exc:
                row = CURRENT.get()
                if row is not None:
                    row["sdk_exception"] = type(exc).__name__
                    for attribute in ("grpc_code", "status_code"):
                        value = getattr(exc, attribute, None)
                        if isinstance(value, int):
                            row["sdk_" + attribute] = value
                raise

        stack.enter_context(patch.object(swoop, "search", sdk_search))

        for module in (httpx, httpx2):
            original = module.AsyncClient.send

            def wrap(send, stream_base):
                class TimedStream(stream_base):
                    def __init__(self, actual, metadata):
                        self.actual, self.metadata = actual, metadata

                    async def __aiter__(self):
                        try:
                            async for chunk in self.actual:
                                yield chunk
                            self.metadata["body_complete"] = True
                        finally:
                            self.metadata.setdefault("body_end", monotonic())

                    async def aclose(self):
                        try:
                            await self.actual.aclose()
                        finally:
                            self.metadata.setdefault("body_end", monotonic())

                async def observed(client, request, **kwargs):
                    row = CURRENT.get()
                    if row is None:
                        return await send(client, request, **kwargs)
                    await self.before_http(row)
                    h = {"start": monotonic(), "method": request.method}
                    try:
                        method = json.loads(request.content).get("method")
                        if method in (
                            "initialize",
                            "tools/call",
                            "notifications/initialized",
                            "tools/list",
                        ):
                            h["rpc"] = method
                    except (ValueError, AttributeError):
                        pass
                    row["http"].append(h)
                    response = await send(client, request, **kwargs)
                    h.update(
                        status=response.status_code,
                        retry_after=response.headers.get("Retry-After"),
                        headers_at=monotonic(),
                    )
                    self.feedback(row, response)
                    if response.is_stream_consumed:
                        h["body_end"] = monotonic()
                        h["body_complete"] = True
                    else:
                        response.stream = TimedStream(response.stream, h)
                    return response

                return observed

            stack.enter_context(
                patch.object(
                    module.AsyncClient, "send", wrap(original, module.AsyncByteStream)
                )
            )
        original_client = rpc._get_client

        class ObservedClient:
            def __init__(client_self, client):
                client_self.actual = client

            def post(client_self, *args, **kwargs):
                row = CURRENT.get()
                if row["provider"] in self.blocked:
                    raise ProviderFailure("benchmark_stopped")
                h = {"start": monotonic(), "rpc": "search"}
                row["http"].append(h)
                response = client_self.actual.post(*args, **kwargs)
                h.update(
                    status=response.status_code,
                    retry_after=response.headers.get("Retry-After"),
                    body_end=monotonic(),
                    body_complete=True,
                )
                self.feedback(row, response)
                return response

            def __getattr__(client_self, name):
                return getattr(client_self.actual, name)

        stack.enter_context(
            patch.object(
                rpc,
                "_get_client",
                lambda *a, **kw: ObservedClient(original_client(*a, **kw)),
            )
        )


class Pool:
    """Experimental bounded pool of production adapter instances, not production code."""

    def __init__(self, factory, count, experiment, batch):
        self.instances = [factory() for _ in range(count)]
        self.provider_id = self.instances[0].provider_id
        self.capabilities = self.instances[0].capabilities
        self.available = asyncio.Queue()
        self.experiment, self.batch = experiment, batch
        for instance in self.instances:
            self.available.put_nowait(instance)

    async def search(self, query):
        if self.provider_id in self.experiment.blocked:
            raise ProviderFailure("benchmark_stopped")
        self.experiment.attempted[self.provider_id] = (
            self.experiment.attempted.get(self.provider_id, 0) + 1
        )
        instance = await self.available.get()
        row = {
            "kind": "call",
            "batch": self.batch,
            "provider": self.provider_id,
            "route": f"{query.origin}-{query.destination}",
            "date": str(query.departure_date),
            "start": monotonic(),
            "utc": datetime.now(UTC).isoformat(),
            "http": [],
            "error": None,
            "offers": 0,
        }
        token = CURRENT.set(row)
        original_invoke = getattr(instance, "_invoke", None)
        if original_invoke:
            # ThreadPoolExecutor.submit does not copy ContextVars. Instrument only
            # this instance's invoke so the real SDK POST can be attributed safely.
            def invoke(*args):
                thread_token = CURRENT.set(row)
                try:
                    return original_invoke(*args)
                finally:
                    CURRENT.reset(thread_token)

            instance._invoke = invoke
        try:
            result = await instance.search(query)
            row["offers"] = sum(map(len, result.offers_by_itinerary_index))
            row["unpriced"] = result.unpriced_candidate_count
            return result
        except BaseException as exc:
            row["error"] = (
                exc.code if isinstance(exc, ProviderFailure) else type(exc).__name__
            )
            row["retry_after_s"] = getattr(exc, "retry_after_seconds", None)
            self.experiment.blocked.add(self.provider_id)
            raise
        finally:
            row["end"] = monotonic()
            row["end_utc"] = datetime.now(UTC).isoformat()
            self.experiment.rows.append(row)
            emit(self.experiment.output, row)
            CURRENT.reset(token)
            if original_invoke:
                instance._invoke = original_invoke
            # A timed-out real thread is never returned to this experimental pool.
            blocking = getattr(instance, "blocking", None)
            if not blocking or not blocking.future or blocking.future.done():
                self.available.put_nowait(instance)

    def close(self):
        for instance in self.instances:
            blocking = getattr(instance, "blocking", None)
            if blocking:
                blocking.close()


class Synthetic(FakeProvider):
    def __init__(self, latency):
        super().__init__(provider_id="synthetic")
        self.latency = latency

    async def search(self, query):
        await asyncio.sleep(self.latency)
        return await super().search(query)


def peak(spans):
    count = maximum = 0
    for _, change in sorted([(a, 1) for a, b in spans] + [(b, -1) for a, b in spans]):
        count += change
        maximum = max(maximum, count)
    return maximum


async def batch(
    experiment,
    engine,
    name,
    factory,
    concurrency,
    interval,
    *,
    live=False,
    n=8,
    poll=0.1,
    seed=48,
    december=False,
    trace=True,
):
    repo = Repository(engine, cache_enabled=False)
    pool = Pool(factory, concurrency, experiment, name)
    reg = Registration(
        pool,
        concurrency=concurrency,
        minimum_interval_seconds=interval,
        live_data=live,
        retention_seconds=900 if live else None,
        timeout_seconds=90 if pool.provider_id == "octotrip" or not live else 30,
    )
    indices = list(range(n))
    random.Random(seed).shuffle(indices)
    jobs = []
    start = monotonic()
    wall_start = datetime.now(UTC).timestamp()
    for idx in indices:
        routes = [("MEL", "DPS"), ("MEL", "SIN"), ("CGK", "DPS"), ("CGK", "SIN")]
        origin, destination = routes[idx % 4]
        departure = date(2027, 1, 19) + timedelta(days=idx // 4)
        if december:
            origin, destination = "MEL", "DPS"
            departure = date(2026, 12, 15) + timedelta(days=idx)
        q = SearchQuery(
            origins=[origin],
            destinations=[destination],
            departure_date_from=departure,
            departure_date_through=departure,
            display_currency="USD",
        )
        jobs.append(
            repo.create_job(
                q,
                [reg],
                max_active=1000,
                max_hourly=10000,
                max_requests=10000,
                max_active_requests=1000,
                budget_seconds=1800,
            ).id
        )
    ready = monotonic()
    runner = JobRunner(repo, [reg], max_attempts=1)
    before = len(experiment.rows)
    ticks, lags, sql_times, busy = [], [], [], []

    def sql_before(conn, cursor, statement, parameters, context, many):
        context._p48_start = monotonic()

    def sql_after(conn, cursor, statement, parameters, context, many):
        sql_times.append(
            (statement.startswith("BEGIN IMMEDIATE"), monotonic() - context._p48_start)
        )

    def sql_error(context):
        busy.append(type(context.original_exception).__name__)

    for hook, callback in [
        ("before_cursor_execute", sql_before),
        ("after_cursor_execute", sql_after),
        ("handle_error", sql_error),
    ]:
        event.listen(engine, hook, callback)

    async def heartbeat():
        while True:
            target = monotonic() + 0.02
            await asyncio.sleep(0.02)
            lags.append(max(0, monotonic() - target))

    monitor = asyncio.create_task(heartbeat())
    cpu_start = resource.getrusage(resource.RUSAGE_SELF)
    if not live and trace:
        tracemalloc.start()
    try:
        while True:
            if live and not live_guard(Path("data/webtest-live.db").resolve()):
                experiment.blocked.add(pool.provider_id)
            if pool.provider_id in experiment.blocked:
                await asyncio.gather(*runner.tasks, return_exceptions=True)
                for job in jobs:
                    repo.cancel(job)
                break
            t = monotonic()
            await runner.tick()
            ticks.append(monotonic() - t)
            with Session(engine) as session:
                active = session.scalar(
                    select(func.count())
                    .select_from(SearchJob)
                    .where(
                        SearchJob.id.in_(jobs),
                        SearchJob.status.in_(("queued", "running")),
                    )
                )
            if not active:
                await asyncio.gather(*runner.tasks)
                break
            await asyncio.sleep(poll)
        elapsed = monotonic() - start
        measured = sorted(
            (r for r in experiment.rows[before:] if r["batch"] == name),
            key=lambda r: r["start"],
        )
        items = [item for job in jobs for item in repo.get_job(job)[1]]
        ok = sum(item.status.startswith("succeeded_") for item in items)
        latency = [r["end"] - r["start"] for r in measured]
        http_spans = [
            (h["start"], h.get("body_end", r["end"]))
            for r in measured
            for h in r["http"]
            if h.get("rpc") in ("tools/call", "search")
        ]
        gaps = [b["start"] - a["start"] for a, b in itertools.pairwise(measured)]
        slots = [ready] * concurrency
        dispatch_delays = []
        last = ready - interval
        for r in measured:
            slot = heapq.heappop(slots)
            dispatch_delays.append(
                max(
                    0,
                    r["start"]
                    - max(slot, last + interval if interval else ready, ready),
                )
            )
            heapq.heappush(slots, r["end"])
            last = r["start"]
        cpu_end = resource.getrusage(resource.RUSAGE_SELF)
        cpu = (
            cpu_end.ru_utime
            + cpu_end.ru_stime
            - cpu_start.ru_utime
            - cpu_start.ru_stime
        )
        result = {
            "kind": "batch",
            "name": name,
            "provider": pool.provider_id,
            "concurrency": concurrency,
            "interval": interval,
            "poll": poll,
            "admission_s": ready - start,
            "n": n,
            "attempted": len(measured),
            "ok": ok,
            "elapsed_s": elapsed,
            "elapsed_wall_s": datetime.now(UTC).timestamp() - wall_start,
            "clock_discontinuity_s": datetime.now(UTC).timestamp()
            - wall_start
            - elapsed,
            "successful_per_minute": 60 * ok / elapsed,
            "ttfr_s": min(
                (r["end"] - start for r in measured if not r["error"]), default=None
            ),
            "latency_p50_s": percentile(latency, 0.5),
            "latency_p95_s": percentile(latency, 0.95),
            "peak_logical": peak([(r["start"], r["end"]) for r in measured]),
            "peak_search_http": peak(http_spans),
            "search_http_response_end_measured": all(
                "body_end" in h
                for r in measured
                for h in r["http"]
                if h.get("rpc") in ("tools/call", "search")
            ),
            "gaps_s": gaps,
            "offers_committed": sum(item.result_count or 0 for item in items),
            "timeouts": sum(
                r["error"] in ("network_timeout", "TimeoutError", "CancelledError")
                for r in measured
            ),
            "http429": sum(h.get("status") == 429 for r in measured for h in r["http"]),
            "errors": [r["error"] for r in measured if r["error"]],
            "stored_errors": [
                {
                    "route": f"{i.origin}-{i.destination}",
                    "date": i.departure_date,
                    "status": i.status,
                    "error": i.last_error_code,
                }
                for i in items
                if not i.status.startswith("succeeded_")
            ],
            "dispatch_delay_p95_s": percentile(dispatch_delays, 0.95),
            "tick_p95_s": percentile(ticks, 0.95),
            "loop_lag_p95_s": percentile(lags, 0.95),
            "loop_lag_max_s": max(lags, default=0),
            "sql_count": len(sql_times),
            "sql_p95_s": percentile([x[1] for x in sql_times], 0.95),
            "sqlite_begin_max_s": max((x[1] for x in sql_times if x[0]), default=0),
            "sql_errors": busy,
            "cpu_seconds": cpu,
            "cpu_one_core_percent": 100 * cpu / (monotonic() - ready),
            "process_peak_rss_bytes": cpu_end.ru_maxrss,
            "python_peak_bytes": tracemalloc.get_traced_memory()[1]
            if not live and trace
            else None,
            "allocation_tracing": not live and trace,
        }
        emit(experiment.output, result)
        return result
    finally:
        if not live and trace:
            tracemalloc.stop()
        monitor.cancel()
        await asyncio.gather(monitor, return_exceptions=True)
        await runner.close()
        pool.close()
        for hook, callback in [
            ("before_cursor_execute", sql_before),
            ("after_cursor_execute", sql_after),
            ("handle_error", sql_error),
        ]:
            event.remove(engine, hook, callback)


def migrated(path):
    url = "sqlite:///" + str(path)
    cfg = Config("backend/alembic.ini")
    cfg.attributes["database_url"] = url
    command.upgrade(cfg, "head")
    return database(url)


async def main(args):
    if Path(args.output).exists():
        raise SystemExit("Output exists; refusing repeat")
    logging.disable(logging.CRITICAL)
    experiment = Experiment(args.output)
    with (
        tempfile.TemporaryDirectory(prefix="p48-throughput-") as temp,
        ExitStack() as stack,
    ):
        if args.mode == "live":
            if not args.run_live or not live_guard(
                Path("data/webtest-live.db").resolve()
            ):
                raise SystemExit("Requires --run-live and idle production queue")
            experiment.instrument(stack)

            async def provider_run(provider, factory):
                engine = migrated(Path(temp) / (provider + ".db"))
                try:
                    base_interval = 0.25 if provider == "swoop" else 1
                    configs = [
                        (1, base_interval),
                        (2, base_interval),
                        (2, 0.5 if provider == "swoop" else 0.25),
                        (1, base_interval),
                    ]
                    if args.profile == "overlap":
                        base_interval = 0.1 if provider == "swoop" else 3
                        configs = [
                            (1, base_interval),
                            (2, base_interval),
                            (2, 0.25 if provider == "swoop" else 5),
                            (1, base_interval),
                        ]
                    if args.profile == "swoop-three":
                        configs = [(2, 0.1), (3, 0.1), (2, 0.1)]
                    if args.profile == "c3-one":
                        configs = [(3, 1)]
                    if args.profile == "swoop-repeat":
                        configs = [(1, 0.1), (2, 0.1), (2, 0.1), (1, 0.1)]
                    results = []
                    for idx, (c, i) in enumerate(configs):
                        if provider in experiment.blocked:
                            break
                        results.append(
                            await batch(
                                experiment,
                                engine,
                                f"{provider}-{idx}-c{c}-i{i}",
                                factory,
                                c,
                                i,
                                live=True,
                                seed=48 + idx,
                                december=provider == "swoop"
                                and args.profile != "initial",
                            )
                        )
                    if (
                        provider != "swoop"
                        and len(results) == 4
                        and all(r["ok"] == 8 for r in results)
                    ):
                        c2 = results[1]
                        baseline = (
                            results[0]["elapsed_s"] + results[3]["elapsed_s"]
                        ) / 2
                        if (
                            c2["peak_search_http"] >= 2
                            and c2["elapsed_s"] < 0.8 * baseline
                        ):
                            await batch(
                                experiment,
                                engine,
                                f"{provider}-4-c3-i{base_interval}",
                                factory,
                                3,
                                base_interval,
                                live=True,
                                seed=52,
                            )
                finally:
                    engine.dispose()

            await asyncio.gather(
                *(
                    provider_run(p, f)
                    for p, f in [
                        ("skiplagged", SkiplaggedProvider),
                        ("swoop", SwoopProvider),
                        ("octotrip", OctotripProvider),
                    ]
                    if p in args.providers
                )
            )
        else:
            engine = migrated(Path(temp) / "synthetic.db")
            try:
                for c in args.concurrencies or (
                    [1, 2, 4, 8, 16, 32] if args.latency == 0.25 else [1, 2, 4, 8]
                ):
                    trial_engine = (
                        migrated(Path(temp) / f"synthetic-c{c}.db")
                        if args.fresh
                        else engine
                    )
                    await batch(
                        experiment,
                        trial_engine,
                        f"synthetic-l{args.latency}-c{c}",
                        lambda: Synthetic(args.latency),
                        c,
                        0,
                        n=64 if args.latency == 0.25 else 8,
                        poll=args.poll,
                        trace=not args.no_trace,
                    )
                    if args.fresh:
                        trial_engine.dispose()
                if args.latency == 0.25 and not args.concurrencies:
                    await batch(
                        experiment,
                        engine,
                        "synthetic-l0.25-c8-poll0.01",
                        lambda: Synthetic(0.25),
                        8,
                        0,
                        n=64,
                        poll=0.01,
                    )
            finally:
                engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["live", "synthetic"], required=True)
    parser.add_argument(
        "--latency", type=float, choices=[0.25, 5, 15, 30], default=0.25
    )
    parser.add_argument("--run-live", action="store_true")
    parser.add_argument(
        "--providers", nargs="+", default=["skiplagged", "swoop", "octotrip"]
    )
    parser.add_argument(
        "--profile",
        choices=["initial", "overlap", "swoop-three", "c3-one", "swoop-repeat"],
        default="initial",
    )
    parser.add_argument("--concurrencies", nargs="+", type=int)
    parser.add_argument("--fresh", action="store_true")
    parser.add_argument("--no-trace", action="store_true")
    parser.add_argument("--poll", type=float, default=0.1)
    parser.add_argument("--output", required=True)
    asyncio.run(main(parser.parse_args()))
