from datetime import UTC, datetime, timedelta

import pytest

from cheapwings.domain.itinerary import IdentityConfidence, Itinerary, compute_fingerprint
from cheapwings.domain.segments import FlightSegment


def _seg(origin, destination, ordinal=0, flight_number="123", hour=8):
    depart = datetime(2026, 12, 16, hour, 0, tzinfo=UTC)
    return FlightSegment(
        marketing_carrier="XY",
        operating_carrier="XY",
        flight_number=flight_number,
        origin=origin,
        destination=destination,
        depart_at=depart,
        arrive_at=depart + timedelta(hours=2),
        ordinal=ordinal,
    )


def test_segment_requires_tz_aware_datetimes():
    with pytest.raises(ValueError):
        FlightSegment(
            marketing_carrier="XY",
            operating_carrier="XY",
            flight_number="123",
            origin="MEL",
            destination="DPS",
            depart_at=datetime(2026, 12, 16, 8, 0),  # naive
            arrive_at=datetime(2026, 12, 16, 13, 0, tzinfo=UTC),
            ordinal=0,
        )


def test_itinerary_requires_connected_segments():
    seg1 = _seg("MEL", "SIN", ordinal=0)
    seg2 = _seg("DPS", "CGK", ordinal=1)  # does not connect from SIN
    with pytest.raises(ValueError):
        Itinerary(
            itinerary_id="x",
            segments=(seg1, seg2),
            identity_confidence=IdentityConfidence.EXACT_SEGMENTS,
        )


def test_identical_segment_sequences_produce_identical_fingerprint():
    a = (_seg("MEL", "DPS"),)
    b = (_seg("MEL", "DPS"),)
    assert compute_fingerprint(a) == compute_fingerprint(b)


def test_different_connections_produce_different_fingerprints():
    a = (_seg("MEL", "SIN", ordinal=0), _seg("SIN", "DPS", ordinal=1, flight_number="456"))
    b = (_seg("MEL", "CGK", ordinal=0), _seg("CGK", "DPS", ordinal=1, flight_number="789"))
    assert compute_fingerprint(a) != compute_fingerprint(b)


def test_stops_and_duration():
    seg1 = _seg("MEL", "SIN", ordinal=0, hour=8)
    seg2 = FlightSegment(
        marketing_carrier="XY",
        operating_carrier="XY",
        flight_number="456",
        origin="SIN",
        destination="DPS",
        depart_at=datetime(2026, 12, 16, 12, 0, tzinfo=UTC),
        arrive_at=datetime(2026, 12, 16, 15, 0, tzinfo=UTC),
        ordinal=1,
    )
    itin = Itinerary(
        itinerary_id="x",
        segments=(seg1, seg2),
        identity_confidence=IdentityConfidence.EXACT_SEGMENTS,
        fingerprint=compute_fingerprint((seg1, seg2)),
    )
    assert itin.stops == 1
    assert itin.duration_minutes == 7 * 60  # 08:00 -> 15:00
