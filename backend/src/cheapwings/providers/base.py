"""Provider abstraction. Components outside adapters deal in canonical values only.

Optional capabilities (calendar, reprice) must not be faked by an adapter
that doesn't actually have them; orchestration branches on advertised
ProviderCapabilities, never on provider name.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol

from cheapwings.domain.coverage import WorkStatus
from cheapwings.domain.itinerary import ItinerarySummary
from cheapwings.domain.offer import Offer, ProviderErrorCode
from cheapwings.domain.segments import FlightSegment


@dataclass(frozen=True, slots=True)
class ProviderCapabilities:
    detailed_search: bool
    calendar: bool
    exact_reprice: bool
    has_booking_link: bool
    has_hidden_city_flag: bool
    has_baggage_details: bool


@dataclass(frozen=True, slots=True)
class SingleDateRouteQuery:
    origin: str
    destination: str
    departure_date: date
    include_basic_economy: bool
    include_hidden_city: bool
    display_currency: str
    point_of_sale_country: str | None = None


@dataclass(frozen=True, slots=True)
class ProviderSearchResult:
    provider_id: str
    requested: SingleDateRouteQuery
    status: WorkStatus
    retrieved_at: datetime
    provider_complete: bool | None
    error_code: ProviderErrorCode | None
    error_detail_sanitized: str | None
    itineraries: tuple[tuple[FlightSegment, ...], ...]
    offers_by_itinerary_index: tuple[tuple[Offer, ...], ...]

    itinerary_summaries: tuple[ItinerarySummary | None, ...] = ()
    unpriced_candidate_count: int = 0

    def __post_init__(self) -> None:
        if self.itinerary_summaries and len(self.itinerary_summaries) != len(self.itineraries):
            raise ValueError("summaries must align with itineraries")
        if len(self.itineraries) != len(self.offers_by_itinerary_index):
            raise ValueError("itineraries and offers_by_itinerary_index must be parallel")
        if self.status == WorkStatus.SUCCEEDED_EMPTY and self.itineraries:
            raise ValueError("succeeded_empty must not carry itineraries")
        if self.status == WorkStatus.FAILED_TERMINAL and self.error_code is None:
            raise ValueError("failed_terminal requires error_code")


class SearchProvider(Protocol):
    provider_id: str
    capabilities: ProviderCapabilities

    async def search(self, query: SingleDateRouteQuery) -> ProviderSearchResult: ...


@dataclass(frozen=True, slots=True)
class RepriceRequest:
    offer: Offer
    segments: tuple[FlightSegment, ...]
    query: SingleDateRouteQuery


@dataclass(frozen=True, slots=True)
class ProviderRepriceResult:
    offers: tuple[Offer, ...]
    segments: tuple[FlightSegment, ...]
    available: bool
    exact_product_match: bool
    warnings: tuple[str, ...] = ()
