"""Safe default ranking ("Best checked deal") plus the "Lowest advertised" alternate view.

Per docs/01 rule 6 and docs/03's ranking tiers:
- hidden_city == yes or unknown is excluded from the default safe ranking.
- comparable totals require comparison_status == eligible_total_known.
- repriced_exact first, then recent_search, then indicative in a separate section.
"""

from __future__ import annotations

from dataclasses import dataclass

import cheapwings_core as _core

from cheapwings.domain.offer import Offer
from cheapwings.engine.matching import ItineraryGroup


@dataclass(frozen=True, slots=True)
class RankedOffer:
    group: ItineraryGroup
    offer: Offer


def _rank(groups: list[ItineraryGroup], *, best: bool) -> list[RankedOffer]:
    candidates = [RankedOffer(g, o) for g in groups for o in g.offers]
    positions = _core.rank_offers(
        [
            (
                r.offer.price_status.value,
                r.offer.hidden_city.value,
                r.offer.comparison_status.value,
                str(r.offer.comparable_amount.amount)
                if r.offer.comparable_amount is not None
                else None,
            )
            for r in candidates
        ],
        best,
    )
    return [candidates[i] for i in positions]


def best_checked_deal(groups: list[ItineraryGroup]) -> list[RankedOffer]:
    """Default view: safe, comparable offers only, tiered by price confidence."""
    return _rank(groups, best=True)


def lowest_advertised(groups: list[ItineraryGroup]) -> list[RankedOffer]:
    """Lowest comparable advertised price, excluding confirmed hidden-city fares."""
    return _rank(groups, best=False)
