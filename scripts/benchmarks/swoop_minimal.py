"""Opt-in SDK-only swoop reproduction; no CheapWings worker, cache or adapter.

Print only counts, timing and up to three price/currency pairs. An SDK empty
result is NOT proof of no inventory: swoop 0.7 can swallow short RPC errors.
"""

import argparse
import json
from importlib.metadata import version
from time import monotonic


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-live", action="store_true")
    parser.add_argument("--origin", default="MEL")
    parser.add_argument("--destination", default="CGK")
    parser.add_argument("--date", default="2026-12-01")
    parser.add_argument("--country", default="ID")
    args = parser.parse_args()
    if not args.run_live:
        parser.error("A single real provider request requires --run-live")

    import swoop

    start = monotonic()
    row = {
        "sdk_version": version("swoop-flights"),
        "origin": args.origin,
        "destination": args.destination,
        "date": args.date,
        "country": args.country,
    }
    try:
        result = swoop.search(
            args.origin,
            args.destination,
            args.date,
            cabin="economy",
            include_basic_economy=True,
            time_budget=25,
            transport=swoop.TransportConfig(
                country=args.country, timeout=20, retries=0
            ),
        )
        row.update(
            sdk_reported_results=len(result.results),
            sdk_complete=result.is_complete,
            sample_fares=[
                {"price": x.price, "currency": x.currency} for x in result.results[:3]
            ],
        )
    except Exception as exc:  # noqa: BLE001 - retain sanitized diagnostic classes only
        row.update(
            error_class=type(exc).__name__,
            http_status=getattr(exc, "status_code", None),
            rpc_status=getattr(exc, "grpc_code", None),
        )
    row["elapsed_s"] = round(monotonic() - start, 3)
    print(json.dumps(row))


if __name__ == "__main__":
    main()
