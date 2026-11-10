"""Flight segments: the atomic unit of itinerary identity.

Per docs/03_PROVIDERS_AGGREGATION_PRICING.md's conservative matching rule,
an itinerary is an ordered sequence of segments, not a route/date string.
Two itineraries with different segments are different itineraries, even if
origin/destination/date match.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class FlightSegment:
    """One flown leg with a stable identity.

    `depart_at`/`arrive_at` must carry explicit UTC offsets; never fabricate
    a missing timezone. `operating_carrier` may equal `marketing_carrier`
    when a provider does not disclose a separate operator.
    """

    marketing_carrier: str
    operating_carrier: str
    flight_number: str
    origin: str
    destination: str
    depart_at: datetime
    arrive_at: datetime
    ordinal: int
    marketing_carrier_name: str | None = None
    operating_carrier_name: str | None = None

    def __post_init__(self) -> None:
        if self.depart_at.tzinfo is None or self.arrive_at.tzinfo is None:
            raise ValueError(
                f"Segment {self.marketing_carrier}{self.flight_number} is missing a UTC "
                "offset on depart_at/arrive_at; never fabricate a timezone."
            )
        if self.origin == self.destination:
            raise ValueError(f"Segment origin and destination are both {self.origin!r}")

    @property
    def identity_key(self) -> tuple:
        """Stable fields used for fingerprinting; excludes anything a provider might refresh."""
        return (
            self.ordinal,
            self.marketing_carrier,
            self.operating_carrier,
            self.flight_number,
            self.origin,
            self.destination,
            self.depart_at.isoformat(),
            self.arrive_at.isoformat(),
        )
