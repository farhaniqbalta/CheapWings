"""P0 feasibility probe for swoop (reverse-engineered Google Flights RPC).

Low-volume, conservative probe: one `search()` call for a documented
example route/date, then (if the search returned a priced result) one
`price_selector()` call to inspect exact-fare repricing behavior. Does not
loop or hammer; a single search + single price call per run.

Usage:
    python scripts/provider_probe_swoop.py

Output: prints summary to stdout and writes a redacted fixture to
contracts/fixtures/provider/swoop_probe_<timestamp>.json
"""

from __future__ import annotations

import dataclasses
import importlib.metadata
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import swoop

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "contracts" / "fixtures" / "provider"

EXAMPLE_ORIGIN = "MEL"
EXAMPLE_DEST = "DPS"
EXAMPLE_DATE = "2026-12-16"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _to_jsonable(obj):
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {k: _to_jsonable(v) for k, v in dataclasses.asdict(obj).items()}
    if isinstance(obj, list):
        return [_to_jsonable(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    return obj


def run() -> dict:
    observed: dict = {
        "provider_id": "swoop",
        "package": "swoop-flights",
        "package_version": importlib.metadata.version("swoop-flights"),
        "probe_run_at": _utc_now_iso(),
        "search_attempted": False,
        "search_result": None,
        "price_attempted": False,
        "price_result": None,
        "basic_economy_search_result": None,
        "errors": [],
    }

    try:
        swoop.set_country("ID")
    except Exception as exc:  # noqa: BLE001
        observed["errors"].append(f"set_country failed: {exc!r}")

    try:
        observed["search_attempted"] = True
        result = swoop.search(
            EXAMPLE_ORIGIN,
            EXAMPLE_DEST,
            EXAMPLE_DATE,
            cabin="economy",
            max_stops=None,
            include_basic_economy=False,
        )
        observed["search_result"] = _to_jsonable(result)
    except Exception as exc:  # noqa: BLE001
        observed["errors"].append(f"search() failed: {exc!r}")
        result = None

    if result is not None and getattr(result, "results", None):
        top = result.results[0]
        selector = getattr(top, "selector", None)
        if selector:
            try:
                observed["price_attempted"] = True
                price_result = swoop.price_selector(selector)
                observed["price_result"] = _to_jsonable(price_result)
            except Exception as exc:  # noqa: BLE001
                observed["errors"].append(f"price_selector() failed: {exc!r}")

    # One additional low-cost check: does include_basic_economy actually
    # change results vs the default (False)? Compare result counts/prices
    # only; do not fetch a second full price_selector call.
    try:
        be_result = swoop.search(
            EXAMPLE_ORIGIN,
            EXAMPLE_DEST,
            EXAMPLE_DATE,
            cabin="economy",
            max_stops=None,
            include_basic_economy=True,
        )
        observed["basic_economy_search_result"] = {
            "result_count": len(be_result.results) if be_result.results else 0,
            "is_complete": be_result.is_complete,
            "cheapest_price": min(
                (t.price for t in be_result.results if t.price is not None),
                default=None,
            )
            if be_result.results
            else None,
        }
    except Exception as exc:  # noqa: BLE001
        observed["errors"].append(f"basic-economy search() failed: {exc!r}")

    return observed


def main() -> int:
    observed = run()
    print(json.dumps(observed, indent=2, default=str))

    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    out_path = FIXTURE_DIR / f"swoop_probe_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps(observed, indent=2, default=str))
    print(f"\nWrote fixture: {out_path}", file=sys.stderr)

    return 0 if not observed["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
