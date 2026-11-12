"""Summarize p412_pool_benchmark JSONL files into P4.9-vs-P4.12 markdown tables."""

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path


def load(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line]


def cell(rows, fn):
    values = sorted(fn(r) for r in rows)
    return statistics.median(values), values[0], values[-1]


def fmt(stats, digits=2):
    med, lo, hi = stats
    return f"{med:.{digits}f} ({lo:.{digits}f}–{hi:.{digits}f})"


METRICS = [
    ("first valid s", lambda r: min(r["first_valid_s"]), 3),
    ("last job done s", lambda r: max(r["job_completion_s"]), 2),
    ("ok ops/min", lambda r: r["successful_ops_per_min"], 0),
    ("op p95 s", lambda r: r["op_latency_p95_s"], 3),
    ("wait p50 s", lambda r: r["admission_wait_p50_s"], 2),
    ("wait p95 s", lambda r: r["admission_wait_p95_s"], 2),
    ("useful util", lambda r: r["useful_slot_utilization"], 2),
    ("peak in-flight", lambda r: r["peak_physical_in_flight"], 0),
    ("CPU s", lambda r: r["cpu_s"], 2),
    ("retries", lambda r: r["retries"], 0),
]


def main(baseline, candidate):
    groups = defaultdict(list)
    for row in load(baseline) + load(candidate):
        groups[(row["scenario"], row["g"], row["variant"])].append(row)
    keys = sorted({(s, g) for s, g, _ in groups}, key=lambda k: (int(k[0].split("_")[0]), k[1]))
    print("| scenario | G | metric | P4.9 C3 median (range) | P4.12 pool median (range) | Δ median |")
    print("|---|---|---|---|---|---|")
    for scenario, g in keys:
        old, new = groups.get((scenario, g, "p49"), []), groups.get((scenario, g, "p412"), [])
        if not old or not new:
            continue
        for label, fn, digits in METRICS:
            a, b = cell(old, fn), cell(new, fn)
            delta = f"{(b[0] - a[0]) / a[0] * 100:+.0f}%" if a[0] else "n/a"
            print(f"| {scenario} | {g} | {label} | {fmt(a, digits)} | {fmt(b, digits)} | {delta} |")
        peaks = defaultdict(lambda: [[], []])
        for i, rows in enumerate((old, new)):
            for r in rows:
                for pid, p in r["providers"].items():
                    peaks[pid][i].append(p["peak_in_flight"])
        detail = "; ".join(f"{pid} {max(a)}→{max(b)}" for pid, (a, b) in sorted(peaks.items()))
        rss = max(r["peak_rss_mb"] for r in new)
        print(f"| {scenario} | {g} | per-provider peak / P4.12 RSS MB | {detail} | {rss} | |")


if __name__ == "__main__":
    main(*sys.argv[1:3])
