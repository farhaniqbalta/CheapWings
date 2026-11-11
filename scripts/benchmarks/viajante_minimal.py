"""Opt-in standalone Viajante query; never imported by production adapters.

Use a temporary environment with viajante installed. One query per invocation,
HTTP sweep only, outer attempts=1. The library may replay a transport failure.
Print no raw page, booking token, selector, cookie, or exception text.
"""

import argparse
import json
import logging
import os
import tempfile
from datetime import date
from importlib.metadata import version
from time import monotonic


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-live", action="store_true")
    parser.add_argument("--origin", default="HND")
    parser.add_argument("--destination", default="CGK")
    parser.add_argument("--date", type=date.fromisoformat, default=date(2026, 11, 20))
    parser.add_argument("--currency", default="IDR")
    parser.add_argument("--country", default="ID")
    args = parser.parse_args()
    if not args.run_live:
        parser.error("A real provider query requires --run-live")
    os.environ["VIAJANTE_STATE_DIR"] = tempfile.mkdtemp(prefix="cheapwings-viajante-")

    from viajante import FlightQuery, orchestration, search_flights

    orchestration.MAX_ATTEMPTS = 1
    logging.disable(logging.CRITICAL)
    started = monotonic()
    row = {
        "version": version("viajante"),
        "origin": args.origin,
        "destination": args.destination,
        "date": args.date.isoformat(),
        "queries": [],
    }
    try:
        report = search_flights(
            [
                FlightQuery(
                    origin=args.origin,
                    destination=args.destination,
                    departure_date=args.date,
                    max_stops=2,
                )
            ],
            currency=args.currency,
            country=args.country,
            fetch="sweep",
            top=3,
            deadline_seconds=30,
        )
        row.update(currency=report.currency, fetch_backend=report.fetch_backend)
        for result in report.queries:
            item = {"status": result.status}
            if result.status == "ok":
                item.update(
                    raw_count=result.raw_count,
                    eligible_count=result.eligible_count,
                    returned_count=len(result.offers),
                    sample_fares=[
                        {"price": o.price, "airline": o.airline, "stops": o.stops_count}
                        for o in result.offers
                    ],
                )
            else:
                error = result.error
                diagnostics = error.diagnostics or {}
                item.update(
                    error_code=error.code.value,
                    rate_limited=error.rate_limited,
                    timeout=error.timeout,
                    http_status=diagnostics.get("http_status"),
                    rpc_status=diagnostics.get("rpc_status"),
                )
            row["queries"].append(item)
    except Exception as exc:  # noqa: BLE001 - sanitized optional SDK diagnostics
        row["exception_class"] = type(exc).__name__
    row["elapsed_s"] = round(monotonic() - started, 3)
    print(json.dumps(row))


if __name__ == "__main__":
    main()
