"""P3 live canary: exercises the REAL SkiplaggedProvider/SwoopProvider adapter
classes (not raw SDK calls) against live endpoints. Low-volume, one-shot,
same route/date as the P0 probes for comparability. Opt-in only; never run
in CI or on a schedule. Owner has already accepted the personal-use risk
conditions recorded in WORK_LOG.md / docs/PROVIDER_POC_REPORT.md.

Usage: python scripts/p3_live_canary.py
"""

import asyncio
import dataclasses
import json
from datetime import date, datetime, timezone

from cheapwings.providers.base import SingleDateRouteQuery
from cheapwings.providers.skiplagged import SkiplaggedProvider
from cheapwings.providers.swoop import SwoopProvider

ORIGIN, DEST, DEPART = "MEL", "DPS", date(2026, 12, 16)


def _jsonable(obj):
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {k: _jsonable(v) for k, v in dataclasses.asdict(obj).items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    return str(obj) if isinstance(obj, datetime) else obj


async def run():
    report = {"run_at": datetime.now(timezone.utc).isoformat(), "providers": {}}

    query = SingleDateRouteQuery(ORIGIN, DEST, DEPART, True, False, "IDR")
    sk = SkiplaggedProvider()
    try:
        result = await sk.search(query)
        report["providers"]["skiplagged"] = {
            "status": result.status.value,
            "offer_count": sum(len(o) for o in result.offers_by_itinerary_index),
            "sample_offer": _jsonable(result.offers_by_itinerary_index[0][0])
            if result.offers_by_itinerary_index else None,
        }
    except Exception as exc:  # noqa: BLE001 - canary script, record and continue
        report["providers"]["skiplagged"] = {"error": repr(exc)}

    sw = SwoopProvider()
    try:
        result = await sw.search(query)
        report["providers"]["swoop"] = {
            "status": result.status.value,
            "offer_count": sum(len(o) for o in result.offers_by_itinerary_index),
            "unpriced_candidate_count": result.unpriced_candidate_count,
            "sample_offer": _jsonable(result.offers_by_itinerary_index[0][0])
            if result.offers_by_itinerary_index else None,
        }
        if result.offers_by_itinerary_index:
            handle = result.offers_by_itinerary_index[0][0].provider_quote_handle
            if handle:
                from cheapwings.providers.base import RepriceRequest
                reprice = await sw.reprice(
                    RepriceRequest(result.offers_by_itinerary_index[0][0],
                                    result.itineraries[0], query)
                )
                report["providers"]["swoop"]["reprice"] = {
                    "available": reprice.available,
                    "exact_product_match": reprice.exact_product_match,
                    "offer_count": len(reprice.offers),
                    "sample_offer": _jsonable(reprice.offers[0]) if reprice.offers else None,
                }
    except Exception as exc:  # noqa: BLE001
        report["providers"]["swoop"] = {"error": repr(exc)}
    finally:
        sw.blocking.close()

    print(json.dumps(report, indent=2, default=str))
    return report


if __name__ == "__main__":
    asyncio.run(run())
