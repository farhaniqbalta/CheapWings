from datetime import UTC, datetime
from decimal import Decimal

import pytest

from cheapwings.domain.money import Money
from cheapwings.domain.offer import ComparisonStatus, LinkScope, Offer, PriceStatus, ThreeValued
from cheapwings.engine.matching import ItineraryGroup, build_itinerary
from cheapwings.engine.ranking import best_checked_deal, lowest_advertised
from tests.unit.test_matching import _seg


def _offer(price, status=PriceStatus.RECENT_SEARCH, hidden_city=ThreeValued.NO,
           comparison_status=ComparisonStatus.ELIGIBLE_TOTAL_KNOWN, quote_id="q", is_estimate=False):
    comparable = Money(Decimal(price), "IDR") if comparison_status == ComparisonStatus.ELIGIBLE_TOTAL_KNOWN else None
    return Offer(
        quote_id=quote_id,
        itinerary_id="",
        provider_id="fake",
        seller="Seller",
        fare_family="standard",
        cabin="economy",
        basic_economy=False,
        amount_original=Money(Decimal(price), "IDR"),
        comparable_amount=comparable,
        comparison_status=comparison_status,
        checked_bag=ThreeValued.YES,
        hidden_city=hidden_city,
        self_transfer=ThreeValued.NO,
        price_status=status,
        is_estimate=is_estimate,
        retrieved_at=datetime.now(UTC),
        repriced_at=None,
        link="https://example.invalid/offer",
        link_scope=LinkScope.GENERIC_SEARCH,
        provider_quote_handle="handle",
    )


def _group(*offers):
    itin = build_itinerary((_seg(),), "itin")
    return ItineraryGroup(itinerary=itin, offers=list(offers))


def test_repriced_exact_ranks_before_recent_search_even_if_pricier():
    cheap_recent = _offer(1_000_000, status=PriceStatus.RECENT_SEARCH, quote_id="q1")
    pricier_exact = _offer(1_500_000, status=PriceStatus.REPRICED_EXACT, quote_id="q2")
    ranked = best_checked_deal([_group(cheap_recent, pricier_exact)])
    assert [r.offer.quote_id for r in ranked] == ["q2", "q1"]


def test_hidden_city_excluded_from_default_ranking():
    unsafe = _offer(500_000, hidden_city=ThreeValued.YES, quote_id="q1")
    unknown = _offer(600_000, hidden_city=ThreeValued.UNKNOWN, quote_id="q2")
    safe = _offer(1_200_000, hidden_city=ThreeValued.NO, quote_id="q3")
    ranked = best_checked_deal([_group(unsafe, unknown, safe)])
    assert [r.offer.quote_id for r in ranked] == ["q3"]


def test_missing_required_baggage_excluded_from_default_ranking():
    incomplete = _offer(
        400_000,
        comparison_status=ComparisonStatus.MISSING_REQUIRED_BAGGAGE,
        quote_id="q1",
    )
    complete = _offer(900_000, quote_id="q2")
    ranked = best_checked_deal([_group(incomplete, complete)])
    assert [r.offer.quote_id for r in ranked] == ["q2"]


def test_lowest_advertised_includes_indicative_but_not_confirmed_hidden_city():
    indicative = _offer(300_000, status=PriceStatus.INDICATIVE, quote_id="q1")
    unsafe = _offer(100_000, hidden_city=ThreeValued.YES, quote_id="q2")
    ranked = lowest_advertised([_group(indicative, unsafe)])
    assert [r.offer.quote_id for r in ranked] == ["q1"]


def test_offer_construction_rejects_repriced_exact_with_estimate_flag():
    with pytest.raises(ValueError):
        _offer(1_000_000, status=PriceStatus.REPRICED_EXACT, is_estimate=True, quote_id="q1")


def test_offer_construction_rejects_hidden_city_in_repriced_exact_tier():
    with pytest.raises(ValueError):
        _offer(
            1_000_000,
            status=PriceStatus.REPRICED_EXACT,
            hidden_city=ThreeValued.UNKNOWN,
            quote_id="q1",
        )
