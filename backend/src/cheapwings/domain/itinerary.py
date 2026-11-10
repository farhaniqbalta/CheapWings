"""Itinerary identity: an ordered sequence of segments with a conservative fingerprint."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from itertools import pairwise

from cheapwings.domain.segments import FlightSegment


class IdentityConfidence(str, Enum):
    EXACT_SEGMENTS = "exact_segments"
    INSUFFICIENT_IDENTITY = "insufficient_identity"


@dataclass(frozen=True, slots=True)
class AirportTransfer:
    """Observed gap between flight airports, without invented ground transport or protection."""

    after_segment: int
    from_airport: str
    to_airport: str


def airport_transfers(segments: tuple[FlightSegment, ...]) -> tuple[AirportTransfer, ...]:
    return tuple(
        AirportTransfer(a.ordinal, a.destination, b.origin)
        for a, b in pairwise(segments)
        if a.destination != b.origin
    )


@dataclass(frozen=True, slots=True)
class ItinerarySummary:
    """Observed routing summary when complete segment identity is unavailable.

    Naive local timestamps are preserved as such; no UTC offset is fabricated.
    """

    origin: str
    destination: str
    depart_at: datetime
    arrive_at: datetime
    duration_minutes: int
    stops: int
    warnings: tuple[str, ...] = ()
    carrier_names: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Itinerary:
    """A complete, ordered flight routing. Not interchangeable with 'route + date'."""

    itinerary_id: str
    segments: tuple[FlightSegment, ...]
    identity_confidence: IdentityConfidence
    fingerprint: str | None = field(default=None)

    summary: ItinerarySummary | None = None
    airport_transfers: tuple[AirportTransfer, ...] = ()

    def __post_init__(self) -> None:
        if self.summary is not None:
            if (
                self.segments
                or self.identity_confidence != IdentityConfidence.INSUFFICIENT_IDENTITY
                or self.fingerprint is not None
                or self.airport_transfers
            ):
                raise ValueError("Summary-only itineraries must remain unmatched without segments")
            return
        if not self.segments:
            raise ValueError("Itinerary must have at least one segment")
        ordered = sorted(self.segments, key=lambda s: s.ordinal)
        if list(ordered) != list(self.segments):
            raise ValueError("Segments must be supplied in ordinal order")
        required = airport_transfers(self.segments)
        if len(set(self.airport_transfers)) != len(self.airport_transfers) or set(required) != set(
            self.airport_transfers
        ):
            raise ValueError(
                "Disconnected flight airports require explicit matching airport transfers"
            )

    @property
    def origin(self) -> str:
        return self.summary.origin if self.summary else self.segments[0].origin

    @property
    def destination(self) -> str:
        return self.summary.destination if self.summary else self.segments[-1].destination

    @property
    def stops(self) -> int:
        return self.summary.stops if self.summary else len(self.segments) - 1

    @property
    def duration_minutes(self) -> int:
        if self.summary:
            return self.summary.duration_minutes
        delta = self.segments[-1].arrive_at - self.segments[0].depart_at
        return int(delta.total_seconds() // 60)


def compute_fingerprint(segments: tuple[FlightSegment, ...]) -> str:
    """Stable fingerprint over ordered segment identity fields.

    Only call this when every segment has complete identity-critical fields
    (flight number, carriers, UTC-aware timestamps, airports). Callers with
    missing/ambiguous identity must use IdentityConfidence.INSUFFICIENT_IDENTITY
    and skip fingerprinting rather than forcing a match.
    """
    canonical = "|".join(
        ",".join(str(part) for part in segment.identity_key) for segment in segments
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
