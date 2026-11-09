"""Conservative itinerary matching per docs/03_PROVIDERS_AGGREGATION_PRICING.md.

Never force-match on route/price/approximate time alone. Identical complete
segment sequences group into one itinerary with multiple offers; anything
with missing/ambiguous segment identity stays a separate unmatched itinerary.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cheapwings.domain.itinerary import IdentityConfidence, Itinerary, compute_fingerprint
from cheapwings.domain.offer import Offer
from cheapwings.domain.segments import FlightSegment


def build_itinerary(segments: tuple[FlightSegment, ...], itinerary_id: str) -> Itinerary:
    """Build an itinerary, fingerprinting only when every segment has complete identity."""
    try:
        fingerprint = compute_fingerprint(segments)
        confidence = IdentityConfidence.EXACT_SEGMENTS
    except (TypeError, AttributeError):
        fingerprint = None
        confidence = IdentityConfidence.INSUFFICIENT_IDENTITY
    return Itinerary(
        itinerary_id=itinerary_id,
        segments=segments,
        identity_confidence=confidence,
        fingerprint=fingerprint,
    )


@dataclass
class ItineraryGroup:
    itinerary: Itinerary
    offers: list[Offer] = field(default_factory=list)


class MatchEngine:
    """Groups itineraries by fingerprint; preserves distinct offers within a group.

    Itineraries with IdentityConfidence.INSUFFICIENT_IDENTITY are never merged
    with anything, even each other, since their segment identity cannot be
    trusted to be equal.
    """

    def __init__(self) -> None:
        self._groups_by_fingerprint: dict[str, ItineraryGroup] = {}
        self._unmatched: list[ItineraryGroup] = []
        self._seen_quote_ids: set[str] = set()

    def add(self, itinerary: Itinerary, offer: Offer) -> None:
        if offer.quote_id in self._seen_quote_ids:
            # Idempotent: duplicate source response for the same quote handle
            # must not inflate result counts.
            return
        self._seen_quote_ids.add(offer.quote_id)

        if itinerary.identity_confidence == IdentityConfidence.INSUFFICIENT_IDENTITY:
            self._unmatched.append(ItineraryGroup(itinerary=itinerary, offers=[offer]))
            return

        assert itinerary.fingerprint is not None
        existing = self._groups_by_fingerprint.get(itinerary.fingerprint)
        if existing is None:
            self._groups_by_fingerprint[itinerary.fingerprint] = ItineraryGroup(
                itinerary=itinerary, offers=[offer]
            )
        else:
            existing.offers.append(offer)

    def groups(self) -> list[ItineraryGroup]:
        return [*self._groups_by_fingerprint.values(), *self._unmatched]
