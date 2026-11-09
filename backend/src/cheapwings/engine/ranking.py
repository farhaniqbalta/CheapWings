"""Safe default ranking ("Best checked deal") plus the "Lowest advertised" alternate view.

Per docs/01 rule 6 and docs/03's ranking tiers:
- hidden_city == yes or unknown is excluded from the default safe ranking.
- comparable totals require comparison_status == eligible_total_known.
- repriced_exact first, then recent_search, then indicative in a separate section.
"""

from __future__ import annotations

from dataclasses import dataclass

from cheapwings.domain.offer import ComparisonStatus, Offer, PriceStatus, ThreeValued
from cheapwings.engine.matching import ItineraryGroup

_TIER_ORDER = {
    PriceStatus.REPRICED_EXACT: 0,
    PriceStatus.RECENT_SEARCH: 1,
    PriceStatus.INDICATIVE: 2,
    PriceStatus.CHANGED_OR_UNAVAILABLE: 3,
}


@dataclass(frozen=True, slots=True)
class RankedOffer:
    group: ItineraryGroup
    offer: Offer


def _is_safe_for_default_ranking(offer: Offer) -> bool:
    if offer.hidden_city != ThreeValued.NO:
        return False
    if offer.comparison_status != ComparisonStatus.ELIGIBLE_TOTAL_KNOWN:
        return False
    if offer.comparable_amount is None:
        return False
    return True


def best_checked_deal(groups: list[ItineraryGroup]) -> list[RankedOffer]:
    """Default view: safe, comparable offers only, tiered by price confidence."""
    candidates = [
        RankedOffer(group=g, offer=o)
        for g in groups
        for o in g.offers
        if _is_safe_for_default_ranking(o)
    ]

    def sort_key(ranked: RankedOffer):
        offer = ranked.offer
        assert offer.comparable_amount is not None
        return (
            _TIER_ORDER[offer.price_status],
            offer.comparable_amount.amount,
        )

    return sorted(candidates, key=sort_key)


def lowest_advertised(groups: list[ItineraryGroup]) -> list[RankedOffer]:
    """Alternate view: cheapest number including unknown-cost/indicative candidates.

    Still excludes confirmed hidden_city == yes, since that is never a normal-
    ticket result; unknown hidden-city risk is surfaced but labeled, not hidden.
    """
    candidates = [
        RankedOffer(group=g, offer=o)
        for g in groups
        for o in g.offers
        if o.hidden_city != ThreeValued.YES and o.comparable_amount is not None
    ]
    return sorted(candidates, key=lambda r: r.offer.comparable_amount.amount)
