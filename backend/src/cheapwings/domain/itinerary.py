"""Itinerary identity: an ordered sequence of segments with a conservative fingerprint."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from cheapwings.domain.segments import FlightSegment


class IdentityConfidence(str, Enum):
    EXACT_SEGMENTS = "exact_segments"
    INSUFFICIENT_IDENTITY = "insufficient_identity"


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


@dataclass(frozen=True, slots=True)
class Itinerary:
    """A complete, ordered flight routing. Not interchangeable with 'route + date'."""

    itinerary_id: str
    segments: tuple[FlightSegment, ...]
    identity_confidence: IdentityConfidence
    fingerprint: str | None = field(default=None)

    summary: ItinerarySummary | None = None

    def __post_init__(self) -> None:
        if self.summary is not None:
            if (self.segments or self.identity_confidence != IdentityConfidence.INSUFFICIENT_IDENTITY
                    or self.fingerprint is not None):
                raise ValueError('Summary-only itineraries must remain unmatched without segments')
            return
        if not self.segments:
            raise ValueError("Itinerary must have at least one segment")
        ordered = sorted(self.segments, key=lambda s: s.ordinal)
        if list(ordered) != list(self.segments):
            raise ValueError("Segments must be supplied in ordinal order")
        for a, b in zip(self.segments, self.segments[1:]):
            if a.destination != b.origin:
                raise ValueError(
                    f"Segment {a.ordinal} arrives at {a.destination} but segment "
                    f"{b.ordinal} departs from {b.origin}; not a connected itinerary"
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
