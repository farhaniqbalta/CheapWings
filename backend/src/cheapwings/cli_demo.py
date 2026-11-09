"""Offline CLI demo: fake-provider vertical slice, no network.

Run with: python -m cheapwings.cli_demo

Prints the P1 acceptance evidence: expanded combinations, per-combo coverage,
matched itinerary groups, and both ranked views. All prices are synthetic
fixtures from FakeProvider, never real fares.
"""

from __future__ import annotations

import asyncio
import dataclasses
import uuid
from datetime import date

from cheapwings.domain.coverage import CoverageEntry, WorkStatus, unique_covered_combinations
from cheapwings.domain.query import SearchQuery
from cheapwings.engine.expansion import expand_routes_and_dates
from cheapwings.engine.matching import MatchEngine, build_itinerary
from cheapwings.engine.ranking import best_checked_deal, lowest_advertised
from cheapwings.providers.base import SingleDateRouteQuery
from cheapwings.providers.fake import FakeProvider, ScriptedOutcome

SYNTHETIC_WARNING = "ALL PRICES BELOW ARE SYNTHETIC FIXTURES, NOT REAL FARES"


async def run_demo() -> None:
    query = SearchQuery(
        origins=["MEL"],
        destinations=["CGK", "DPS", "SUB"],
        departure_date_from=date(2026, 12, 12),
        departure_date_through=date(2026, 12, 20),
        display_currency="IDR",
    )
    combos = expand_routes_and_dates(query)
    print(f"Expanded {len(combos)} route-date combinations (expected 27 for 1x3x9).\n")

    providers = [FakeProvider(provider_id="fake_a", base_price_usd=280),
                 FakeProvider(provider_id="fake_b", base_price_usd=250)]
    # Script one failure and one empty result to prove partial-coverage honesty.
    providers[0].script(
        "MEL", "SUB", date(2026, 12, 15),
        ScriptedOutcome(status=WorkStatus.FAILED_TERMINAL),
    )
    providers[1].script(
        "MEL", "CGK", date(2026, 12, 13),
        ScriptedOutcome(status=WorkStatus.SUCCEEDED_EMPTY),
    )

    match_engine = MatchEngine()
    coverage: list[CoverageEntry] = []

    for combo in combos:
        for provider in providers:
            pq = SingleDateRouteQuery(
                origin=combo.origin,
                destination=combo.destination,
                departure_date=combo.departure_date,
                include_basic_economy=query.include_basic_economy,
                include_hidden_city=query.include_hidden_city,
                display_currency=query.display_currency,
            )
            result = await provider.search(pq)
            coverage.append(
                CoverageEntry(
                    provider_id=provider.provider_id,
                    origin=combo.origin,
                    destination=combo.destination,
                    departure_date=combo.departure_date,
                    status=result.status,
                    attempts=1,
                    error_code=result.error_code,
                    error_detail_sanitized=result.error_detail_sanitized,
                    result_count=sum(len(o) for o in result.offers_by_itinerary_index) or None,
                    provider_complete=result.provider_complete,
                    started_at=result.retrieved_at,
                    finished_at=result.retrieved_at,
                )
            )
            for segments, offers in zip(result.itineraries, result.offers_by_itinerary_index):
                itinerary_id = str(uuid.uuid4())
                itinerary = build_itinerary(segments, itinerary_id)
                for offer in offers:
                    match_engine.add(itinerary, dataclasses.replace(offer, itinerary_id=itinerary.itinerary_id))

    total_combos = len(combos) * len(providers)
    succeeded = sum(
        1 for c in coverage if c.status in (WorkStatus.SUCCEEDED_RESULTS, WorkStatus.SUCCEEDED_EMPTY)
    )
    failed = sum(1 for c in coverage if c.status == WorkStatus.FAILED_TERMINAL)
    print(f"Provider work items: {total_combos} total, {succeeded} succeeded, {failed} failed")
    print(f"Unique route-date combinations covered: {unique_covered_combinations(coverage)}/{len(combos)}\n")

    groups = match_engine.groups()
    print(f"Matched itinerary groups: {len(groups)}\n")

    print(f"--- Best checked deal (safe, ranked) --- [{SYNTHETIC_WARNING}]")
    for ranked in best_checked_deal(groups)[:5]:
        itin = ranked.group.itinerary
        offer = ranked.offer
        print(
            f"  {offer.amount_original} | {itin.origin}->{itin.destination} "
            f"{itin.segments[0].depart_at.date()} | {offer.price_status.value} | {offer.seller}"
        )

    print(f"\n--- Lowest advertised --- [{SYNTHETIC_WARNING}]")
    for ranked in lowest_advertised(groups)[:5]:
        itin = ranked.group.itinerary
        offer = ranked.offer
        print(
            f"  {offer.amount_original} | {itin.origin}->{itin.destination} "
            f"{itin.segments[0].depart_at.date()} | {offer.price_status.value} | {offer.seller}"
        )


def main() -> None:
    asyncio.run(run_demo())


if __name__ == "__main__":
    main()
