"""P7.1 addendum: owner-approved, low-volume probe of Fli's Google Flights Explore.

Needs upstream Fli with `SearchExplore` (commit af5d0ed or later) in a separate
virtualenv; the backend keeps its pinned Fli. Each call is one origin and one
departure date to ANYWHERE, one-way. Fli retries Google's transient error 13,
so attempts are capped at 2 per call (12 requests for the 6 approved calls).
Calls are 60 s apart; the probe stops at the first non-transient refusal.

Usage:
    python scripts/provider_probe_fli_explore.py --i-have-owner-approval

Output: contracts/fixtures/provider/fli_explore_p71_<timestamp>.json, keeping
the destination, price and flight fields; booking tokens and images are dropped.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import fli.search.explore as explore_module
from fli.models import Airport, ExploreRegion, ExploreSearchFilters
from fli.search import SearchExplore
from fli.search.exceptions import SearchParseError, SearchRejectedError

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "contracts" / "fixtures" / "provider"
CALLS = [(o, d) for d in ("2026-12-22", "2027-01-26") for o in ("CGK", "SUB", "DPS")]
ATTEMPTS_PER_CALL = 2
CALL_SPACING_S = 60
KEEP = (
    "name", "country", "destination_airport", "departure_date", "arrival_date",
    "price", "currency", "airline", "airline_name", "stops", "duration_minutes",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--i-have-owner-approval", action="store_true", required=True)
    parser.parse_args()

    explore_module.EXPLORE_ATTEMPTS = ATTEMPTS_PER_CALL
    attempts = {"n": 0}
    search_once = SearchExplore._search_once

    def counted(self, *args, **kwargs):
        attempts["n"] += 1
        return search_once(self, *args, **kwargs)

    SearchExplore._search_once = counted
    observed = {"provider_id": "fli_explore", "fli_commit": "af5d0ed", "probe_run_at": datetime.now(timezone.utc).isoformat(), "calls": [], "stopped": None}
    searcher = SearchExplore()
    for i, (origin, date) in enumerate(CALLS):
        if i:
            time.sleep(CALL_SPACING_S)
        before, started = attempts["n"], time.monotonic()
        entry = {"origin": origin, "departure_date": date, "currency": "IDR"}
        try:
            filters = ExploreSearchFilters(origin=Airport[origin], destination=ExploreRegion.ANYWHERE, departure_date=date)
            result = searcher.search(filters, currency="IDR")
            rows = [{k: getattr(d, k, None) for k in KEEP} for d in result.destinations]
            entry.update(origin_name=result.origin_name, destinations=len(rows),
                         priced=sum(r["price"] is not None for r in rows), rows=rows)
        except SearchRejectedError as exc:
            entry["rejected"] = {"code": getattr(exc, "code", None), "retryable": getattr(exc, "retryable", None), "detail": str(exc)[:300]}
        except (SearchParseError, Exception) as exc:  # noqa: BLE001 - probe script, record and stop
            entry["exception"] = repr(exc)[:300]
        entry["attempts"] = attempts["n"] - before
        entry["latency_ms"] = round((time.monotonic() - started) * 1000)
        observed["calls"].append(entry)
        print(f"[{i + 1}/{len(CALLS)}] {origin} {date} attempts={entry['attempts']} "
              f"priced={entry.get('priced')} {entry.get('rejected') or entry.get('exception') or ''}", file=sys.stderr)
        transient = entry.get("rejected", {}).get("retryable")
        if "exception" in entry or ("rejected" in entry and not transient):
            observed["stopped"] = f"call {i + 1}"
            break
    observed["total_requests"] = attempts["n"]
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    out = FIXTURE_DIR / f"fli_explore_p71_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(observed, indent=2, default=str))
    print(f"Wrote {out}; requests={attempts['n']} stopped={observed['stopped']}", file=sys.stderr)
    return 0 if observed["stopped"] is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
