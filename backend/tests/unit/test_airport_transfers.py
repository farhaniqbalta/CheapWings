"""Synthetic regressions for the live-observed NRT→HND airport-change failure shape."""

from dataclasses import replace
from datetime import UTC, datetime

import pytest

from cheapwings.domain.itinerary import (
    AirportTransfer,
    IdentityConfidence,
    Itinerary,
    compute_fingerprint,
)
from cheapwings.domain.segments import FlightSegment


def segments():
    first = FlightSegment(
        "JL",
        "JL",
        "720",
        "CGK",
        "NRT",
        datetime(2026, 12, 15, 1, tzinfo=UTC),
        datetime(2026, 12, 15, 8, tzinfo=UTC),
        0,
    )
    second = FlightSegment(
        "JL",
        "JL",
        "529",
        "HND",
        "CTS",
        datetime(2026, 12, 15, 11, tzinfo=UTC),
        datetime(2026, 12, 15, 13, tzinfo=UTC),
        1,
    )
    return first, second


def test_explicit_airport_change_retains_flight_identity_without_fake_leg():
    legs = segments()
    routing = Itinerary(
        "synthetic",
        legs,
        IdentityConfidence.EXACT_SEGMENTS,
        compute_fingerprint(legs),
        airport_transfers=(AirportTransfer(0, "NRT", "HND"),),
    )
    assert len(routing.segments) == 2
    assert routing.stops == 1
    assert routing.duration_minutes == 720
    assert routing.airport_transfers[0].from_airport == "NRT"


@pytest.mark.parametrize(
    "transfers",
    [
        (),
        (AirportTransfer(0, "NRT", "TPE"),),
        (AirportTransfer(1, "NRT", "HND"),),
        (AirportTransfer(0, "NRT", "HND"), AirportTransfer(0, "NRT", "HND")),
    ],
)
def test_undeclared_or_mismatched_airport_changes_stay_invalid(transfers):
    with pytest.raises(ValueError):
        Itinerary(
            "synthetic", segments(), IdentityConfidence.EXACT_SEGMENTS, airport_transfers=transfers
        )


def test_display_names_do_not_change_itinerary_fingerprint():
    legs = segments()
    named = tuple(replace(s, marketing_carrier_name="Japan Airlines") for s in legs)
    assert compute_fingerprint(legs) == compute_fingerprint(named)
