from datetime import UTC, datetime, timedelta
from decimal import Decimal

from cheapwings.domain.itinerary import IdentityConfidence, Itinerary
from cheapwings.domain.money import Money
from cheapwings.domain.offer import ComparisonStatus, LinkScope, Offer, PriceStatus, ThreeValued
from cheapwings.domain.segments import FlightSegment
from cheapwings.engine.matching import MatchEngine, build_itinerary


def _seg(origin="MEL", destination="DPS", flight_number="123"):
    depart = datetime(2026, 12, 16, 8, 0, tzinfo=UTC)
    return FlightSegment(
        marketing_carrier="XY",
        operating_carrier="XY",
        flight_number=flight_number,
        origin=origin,
        destination=destination,
        depart_at=depart,
        arrive_at=depart + timedelta(hours=5),
        ordinal=0,
    )


def _offer(quote_id, provider_id, price=Decimal(2850000), seller="Seller A"):
    return Offer(
        quote_id=quote_id,
        itinerary_id="",
        provider_id=provider_id,
        seller=seller,
        fare_family="standard",
        cabin="economy",
        basic_economy=False,
        amount_original=Money(price, "IDR"),
        comparable_amount=Money(price, "IDR"),
        comparison_status=ComparisonStatus.ELIGIBLE_TOTAL_KNOWN,
        checked_bag=ThreeValued.YES,
        hidden_city=ThreeValued.NO,
        self_transfer=ThreeValued.NO,
        price_status=PriceStatus.RECENT_SEARCH,
        is_estimate=False,
        retrieved_at=datetime.now(UTC),
        repriced_at=None,
        link="https://example.invalid/offer",
        link_scope=LinkScope.GENERIC_SEARCH,
        provider_quote_handle="handle",
    )


def test_same_itinerary_two_providers_groups_with_distinct_offers():
    engine = MatchEngine()
    itin_a = build_itinerary((_seg(),), "a")
    itin_b = build_itinerary((_seg(),), "b")  # identical segments, different id

    engine.add(itin_a, _offer("q1", "skiplagged"))
    engine.add(itin_b, _offer("q2", "swoop", seller="Seller B"))

    groups = engine.groups()
    assert len(groups) == 1
    assert len(groups[0].offers) == 2


def test_different_connections_are_different_itineraries():
    engine = MatchEngine()
    itin_direct = build_itinerary((_seg(flight_number="123"),), "a")
    itin_other = build_itinerary((_seg(flight_number="456"),), "b")

    engine.add(itin_direct, _offer("q1", "skiplagged"))
    engine.add(itin_other, _offer("q2", "swoop"))

    groups = engine.groups()
    assert len(groups) == 2


def test_duplicate_quote_response_is_idempotent():
    engine = MatchEngine()
    itin = build_itinerary((_seg(),), "a")
    offer = _offer("q1", "swoop")

    engine.add(itin, offer)
    engine.add(itin, offer)  # same quote_id, e.g. a retry delivering the same response

    groups = engine.groups()
    assert len(groups) == 1
    assert len(groups[0].offers) == 1


def test_insufficient_identity_itineraries_never_merge():
    engine = MatchEngine()
    itin1 = Itinerary(
        itinerary_id="x",
        segments=(_seg(),),
        identity_confidence=IdentityConfidence.INSUFFICIENT_IDENTITY,
        fingerprint=None,
    )
    itin2 = Itinerary(
        itinerary_id="y",
        segments=(_seg(),),
        identity_confidence=IdentityConfidence.INSUFFICIENT_IDENTITY,
        fingerprint=None,
    )
    engine.add(itin1, _offer("q1", "skiplagged"))
    engine.add(itin2, _offer("q2", "skiplagged"))

    groups = engine.groups()
    assert len(groups) == 2
