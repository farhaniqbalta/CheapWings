"""P4.12 offline benchmark: P4.9 per-provider C3 versus the shared global pool.

Synthetic adapters only; no network. Runs the production JobRunner, Repository
and SQLite schema of whichever source tree is first on PYTHONPATH. P4.9 is
measured by pointing PYTHONPATH at a worktree of the P4.9 baseline; there
`Registration` still has `concurrency`, set to the shipped C3. Results are a
model of scheduler behaviour, not a forecast of live provider throughput.

    PYTHONPATH=backend/src python scripts/benchmarks/p412_pool_benchmark.py --label p412
    PYTHONPATH=<p49-worktree>/backend/src python ... --label p49
"""

import argparse
import asyncio
import dataclasses
import itertools
import json
import math
import random
import resource
import statistics
import tempfile
import time
from datetime import date, timedelta
from pathlib import Path
from time import monotonic

from alembic import command
from alembic.config import Config
from cheapwings.application.job_runner import JobRunner
from cheapwings.domain.evidence import ProviderFailure
from cheapwings.domain.query import SearchQuery
from cheapwings.providers.fake import FakeProvider
from cheapwings.providers.registry import Registration
from cheapwings.providers.swoop import BoundedCall
from cheapwings.storage.db import database
from cheapwings.storage.repository import Repository

BASELINE = "concurrency" in {f.name for f in dataclasses.fields(Registration)}
C3 = 3  # P4.9 shipped per-provider ceiling (owner-approved defaults)
DESTS = ["DPS", "CGK", "SUB", "SIN"]


def quantile(values, q):
    return sorted(values)[max(0, math.ceil(q * len(values)) - 1)] if values else None


def migrated(path):
    cfg = Config("backend/alembic.ini")
    cfg.attributes["database_url"] = "sqlite:///" + str(path)
    command.upgrade(cfg, "head")
    return database(cfg.attributes["database_url"])


def query(n, offset=0):
    """n route-date items: up to four destinations x consecutive dates."""
    dests = DESTS[: min(4, n)]
    days = math.ceil(n / len(dests))
    first = date(2027, 3, 1) + timedelta(days=offset)
    return SearchQuery(
        origins=["MEL"],
        destinations=dests,
        departure_date_from=first,
        departure_date_through=first + timedelta(days=days - 1),
        display_currency="USD",
        max_combinations=max(120, len(dests) * days),
    )


class Synth(FakeProvider):
    """Deterministic latency; optional 429s; optional real blocking thread."""

    def __init__(self, pid, mean, trace, *, fail_first=0, threads=None, seed=0):
        super().__init__(provider_id=pid)
        self.mean, self.trace, self.fail_first = mean, trace, fail_first
        self.rng = random.Random(seed)
        self.calls = 0
        if threads:
            self.blocking = BoundedCall(threads)

    async def search(self, q):
        self.calls += 1
        number = self.calls
        latency = self.mean * self.rng.uniform(0.7, 1.3)
        row = {"provider": self.provider_id, "start": monotonic(), "ok": False}
        self.trace.append(row)
        try:
            if hasattr(self, "blocking"):
                await self.blocking.run(time.sleep, latency)
            else:
                await asyncio.sleep(latency)
            if number <= self.fail_first:
                raise ProviderFailure("http_rate_limited", 1)
            result = await super().search(q)
            row["ok"] = True
            return result
        finally:
            row["end"] = monotonic()


def reg(provider, interval):
    extra = {"concurrency": C3} if BASELINE else {}
    return Registration(provider, minimum_interval_seconds=interval, **extra)


def threads(g):
    # P4.9 sized a blocking adapter's pool to its C3 setting; P4.12 sizes it to G.
    return C3 if BASELINE else g


def peak(rows):
    events = sorted([(r["start"], 1) for r in rows] + [(r["end"], -1) for r in rows])
    count = top = 0
    for _, delta in events:
        count += delta
        top = max(top, count)
    return top


# Each scenario: (providers spec, jobs spec, options). Latency/intervals are
# scaled ~0.05x of observed live values (P4.9 replay convention).
def scenario(name, g, trace, seed):
    s = lambda pid, mean, **kw: Synth(pid, mean, trace, seed=seed, **kw)
    if name == "1_single_provider":
        p = [(s("a", 0.3), 0.01)]
        return p, [(60, [0], 0, 0)], {}
    if name == "2_two_latencies":
        p = [(s("fast", 0.1), 0.01), (s("slow", 0.8), 0.01)]
        return p, [(40, [0, 1], 0, 0)], {}
    if name == "3_three_intervals":
        p = [(s(x, 0.4), i) for x, i in (("a", 0.05), ("b", 0.15), ("c", 0.25))]
        return p, [(30, [0, 1, 2], 0, 0)], {}
    if name == "4_slow_then_fast_new_work":
        p = [(s("slow", 1.5), 0.01), (s("fast", 0.1), 0.01)]
        return p, [(24, [0], 0, 0), (24, [1], 0.2, 40)], {}
    if name == "5_cooldown":
        p = [(s("cooled", 0.2, fail_first=2), 0.01), (s("ok", 0.2), 0.01)]
        return p, [(24, [0, 1], 0, 0)], {}
    if name == "6_shared_and_cache":
        p = [(s("a", 0.3), 0.01), (s("b", 0.3), 0.01)]
        return p, [(24, [0, 1], 0, 0), (24, [0, 1], 0.05, 0)], {"cache": True}
    if name == "7_cancel_unfinished_io":
        p = [(s("blk", 0.4, threads=threads(g)), 0.0), (s("async", 0.2), 0.01)]
        return p, [(24, [0], 0, 0), (24, [1], 0.1, 40)], {"cancel": (0, 0.15)}
    if name == "8_restart":
        p = [(s("a", 0.3), 0.01), (s("b", 0.3), 0.01)]
        return p, [(40, [0, 1], 0, 0)], {"restart_at": 0.4}
    if name == "9_large_vs_small":
        p = [(s("a", 0.3), 0.01), (s("b", 0.3), 0.01)]
        jobs = [(80, [0, 1], 0, 0)] + [(4, [0, 1], 0.1, 100 + 5 * k) for k in range(4)]
        return p, jobs, {}
    if name == "10_g100_stress":
        p = [(s(x, 0.2), 0.0) for x in ("a", "b", "c", "d")]
        return p, [(400, [0, 1, 2, 3], 0, 0)], {}
    raise ValueError(name)


SCENARIOS = [
    "1_single_provider",
    "2_two_latencies",
    "3_three_intervals",
    "4_slow_then_fast_new_work",
    "5_cooldown",
    "6_shared_and_cache",
    "7_cancel_unfinished_io",
    "8_restart",
    "9_large_vs_small",
    "10_g100_stress",
]


async def trial(name, g, repeat, directory):
    trace = []
    providers, jobs, opts = scenario(name, g, trace, seed=repeat)
    regs = [reg(p, i) for p, i in providers]
    engine = migrated(Path(directory) / f"{name}-{g}-{repeat}.db")
    repo = Repository(engine, global_capacity=g, cache_enabled=opts.get("cache", False))
    # Short timeouts keep runs bounded; claim leases are still timeout + 10s.
    timing = {"timeout_seconds": 3, "lease_seconds": 4, "max_in_flight": g}
    runner = JobRunner(repo, regs, **timing)
    usage0, t0 = resource.getrusage(resource.RUSAGE_SELF), monotonic()
    pending = sorted(enumerate(jobs), key=lambda x: x[1][2])
    created, peak_occupied, restarted, cancelled = {}, 0, False, False
    deadline = t0 + 120
    while monotonic() < deadline:
        now = monotonic() - t0
        while pending and pending[0][1][2] <= now:
            index, (n, which, _, offset) = pending.pop(0)
            created[index] = repo.create_job(
                query(n, offset),
                [regs[i] for i in which],
                max_active=10,
                max_hourly=1000,
            ).id
        if "cancel" in opts and not cancelled and now >= opts["cancel"][1]:
            repo.cancel(created[opts["cancel"][0]])
            cancelled = True
        if "restart_at" in opts and not restarted and now >= opts["restart_at"]:
            await runner.close()  # graceful stop: drains real I/O, leaves leases
            repo = Repository(
                engine, global_capacity=g, cache_enabled=opts.get("cache", False)
            )
            runner = JobRunner(repo, regs, **timing)
            restarted = True
        await runner.tick()
        peak_occupied = max(peak_occupied, runner.occupied())
        if (
            not pending
            and not runner.tasks
            and all(
                repo.get_job(j)[0].status not in ("queued", "running")
                for j in created.values()
            )
        ):
            break
        await runner.pause()
    await runner.close()
    wall = monotonic() - t0
    usage1 = resource.getrusage(resource.RUSAGE_SELF)

    ttfr, completion, waits, attempts, failed = [], [], [], 0, 0
    for index, job_id in created.items():
        job, items = repo.get_job(job_id)
        done = [
            i.finished_at
            for i in items
            if i.status == "succeeded_results" and i.finished_at
        ]
        if done:
            ttfr.append((min(done) - job.created_at) / 1000)
            completion.append((max(done) - job.created_at) / 1000)
        waits += [(i.started_at - job.created_at) / 1000 for i in items if i.started_at]
        attempts += sum(max(0, (i.attempts or 0) - 1) for i in items)
        failed += sum(i.status == "failed_terminal" for i in items)
    ops = [r for r in trace if "end" in r]
    ok = [r for r in ops if r["ok"]]
    latencies = [r["end"] - r["start"] for r in ops]
    by_provider = {}
    for pid, rows in itertools.groupby(
        sorted(ops, key=lambda r: r["provider"]), lambda r: r["provider"]
    ):
        rows = sorted(rows, key=lambda r: r["start"])
        gaps = [b["start"] - a["start"] for a, b in itertools.pairwise(rows)]
        by_provider[pid] = {
            "calls": len(rows),
            "peak_in_flight": peak(rows),
            "min_start_gap_s": round(min(gaps), 4) if gaps else None,
        }
    intervals = {p.provider_id: i for p, i in providers}
    for pid, stats in by_provider.items():
        gap = stats["min_start_gap_s"]
        # Actual adapter-entry pacing must hold (1ms clock slack).
        assert gap is None or gap >= intervals[pid] - 0.001, (name, g, pid, gap)
    busy = sum(latencies)
    return {
        "variant": "p49" if BASELINE else "p412",
        "scenario": name,
        "g": g,
        "repeat": repeat,
        "wall_s": round(wall, 3),
        "first_valid_s": [round(x, 3) for x in sorted(ttfr)],
        "job_completion_s": [round(x, 3) for x in sorted(completion)],
        "successful_ops_per_min": round(len(ok) / wall * 60, 1),
        "op_latency_p50_s": round(quantile(latencies, 0.5) or 0, 3),
        "op_latency_p95_s": round(quantile(latencies, 0.95) or 0, 3),
        "admission_wait_p50_s": round(quantile(waits, 0.5) or 0, 3),
        "admission_wait_p95_s": round(quantile(waits, 0.95) or 0, 3),
        "useful_slot_utilization": round(
            sum(r["end"] - r["start"] for r in ok) / (g * wall), 3
        ),
        "busy_slot_utilization": round(busy / (g * wall), 3),
        "peak_physical_in_flight": max(peak(ops), peak_occupied),
        "providers": by_provider,
        "cpu_s": round(
            (usage1.ru_utime - usage0.ru_utime) + (usage1.ru_stime - usage0.ru_stime), 3
        ),
        "peak_rss_mb": round(
            usage1.ru_maxrss / (1024 * 1024), 1
        ),  # macOS reports bytes
        "retries": attempts,
        "failed_terminal": failed,
        "physical_calls": len(ops),
    }


def summarize(rows):
    def med(key):
        return round(statistics.median(r[key] for r in rows), 3)

    return {
        "n": len(rows),
        "wall_s_median": med("wall_s"),
        "wall_s_range": [
            min(r["wall_s"] for r in rows),
            max(r["wall_s"] for r in rows),
        ],
        "first_valid_s_median": round(
            statistics.median(min(r["first_valid_s"]) for r in rows), 3
        ),
        "ops_per_min_median": med("successful_ops_per_min"),
        "useful_util_median": med("useful_slot_utilization"),
        "peak_in_flight_max": max(r["peak_physical_in_flight"] for r in rows),
    }


async def main(args):
    out = Path(args.out)
    cells = [
        (name, g)
        for name in args.scenarios
        for g in ([100] if name == "10_g100_stress" else args.capacities)
    ]
    rows = {cell: [] for cell in cells}
    stop_at = monotonic() + args.time_limit
    with tempfile.TemporaryDirectory() as directory:
        # Repeat-major order: a time limit still leaves every cell covered.
        for repeat in range(args.repeats):
            if monotonic() >= stop_at:
                break
            for name, g in cells:
                if monotonic() >= stop_at:
                    print(f"time limit reached during repeat {repeat}", flush=True)
                    break
                row = await trial(name, g, repeat, directory)
                rows[(name, g)].append(row)
                with out.open("a") as stream:  # noqa: ASYNC230 - tiny offline append
                    stream.write(json.dumps(row, sort_keys=True) + "\n")
                # Invariants, not just measurements.
                assert row["peak_physical_in_flight"] <= g, row
            print(f"repeat {repeat} done", flush=True)
    for (name, g), cell_rows in rows.items():
        if cell_rows:
            print(name, f"G{g}", json.dumps(summarize(cell_rows)), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--capacities", type=int, nargs="+", default=[9, 16, 32, 64])
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--scenarios", nargs="+", default=SCENARIOS)
    parser.add_argument("--out", default=None)
    parser.add_argument("--time-limit", type=float, default=900, help="seconds per run")
    a = parser.parse_args()
    a.out = a.out or f"scripts/benchmarks/artifacts/p412_{a.label}.jsonl"
    asyncio.run(main(a))
