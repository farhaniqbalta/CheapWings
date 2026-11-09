"""Deterministic fake provider for offline testing. All prices are synthetic fixtures."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from cheapwings.domain.coverage import WorkStatus
from cheapwings.domain.money import Money, minor_unit_exponent
from cheapwings.domain.offer import (
    ComparisonStatus,
    LinkScope,
    Offer,
    PriceStatus,
    ProviderErrorCode,
    ThreeValued,
)
from cheapwings.domain.segments import FlightSegment
from cheapwings.providers.base import (
    ProviderCapabilities,
    ProviderSearchResult,
    SingleDateRouteQuery,
)

SYNTHETIC_LABEL = "SYNTHETIC-FIXTURE-NOT-A-REAL-FARE"


@dataclass(frozen=True, slots=True)
class ScriptedOutcome:
    """Forces a specific outcome for one route-date combo, for error/timeout tests."""

    status: WorkStatus
    error_code: ProviderErrorCode | None = None
    delay_seconds: float = 0.0


@dataclass
class FakeProvider:
    provider_id: str = "fake"
    base_price_usd: int = 300
    capabilities: ProviderCapabilities = field(
        default_factory=lambda: ProviderCapabilities(
            detailed_search=True,
            calendar=False,
            exact_reprice=False,
            has_booking_link=True,
            has_hidden_city_flag=True,
            has_baggage_details=True,
        )
    )
    scripted_outcomes: dict[tuple[str, str, str], ScriptedOutcome] = field(default_factory=dict)

    def script(
        self,
        origin: str,
        destination: str,
        departure_date,
        outcome: ScriptedOutcome,
    ) -> None:
        self.scripted_outcomes[(origin, destination, str(departure_date))] = outcome

    def _deterministic_price(self, query: SingleDateRouteQuery, seller_index: int) -> Decimal:
        key = f"{query.origin}{query.destination}{query.departure_date}{seller_index}"
        digest_value = sum(ord(c) for c in key)
        exponent = minor_unit_exponent(query.display_currency)
        minor_units = (digest_value % 50000) + self.base_price_usd * (10**exponent)
        return Decimal(minor_units).scaleb(-exponent)

    async def search(self, query: SingleDateRouteQuery) -> ProviderSearchResult:
        key = (query.origin, query.destination, str(query.departure_date))
        scripted = self.scripted_outcomes.get(key)
        if scripted and scripted.delay_seconds:
            await asyncio.sleep(scripted.delay_seconds)

        retrieved_at = datetime.now(UTC)

        if scripted and scripted.status == WorkStatus.FAILED_TERMINAL:
            return ProviderSearchResult(
                provider_id=self.provider_id,
                requested=query,
                status=WorkStatus.FAILED_TERMINAL,
                retrieved_at=retrieved_at,
                provider_complete=None,
                error_code=scripted.error_code or ProviderErrorCode.UNKNOWN,
                error_detail_sanitized="scripted failure for test fixture",
                itineraries=(),
                offers_by_itinerary_index=(),
            )

        if scripted and scripted.status == WorkStatus.SUCCEEDED_EMPTY:
            return ProviderSearchResult(
                provider_id=self.provider_id,
                requested=query,
                status=WorkStatus.SUCCEEDED_EMPTY,
                retrieved_at=retrieved_at,
                provider_complete=True,
                error_code=None,
                error_detail_sanitized=None,
                itineraries=(),
                offers_by_itinerary_index=(),
            )

        depart_at = datetime(
            query.departure_date.year,
            query.departure_date.month,
            query.departure_date.day,
            8,
            0,
            tzinfo=UTC,
        )
        arrive_at = depart_at + timedelta(hours=5)
        segments = (
            FlightSegment(
                marketing_carrier="FX",
                operating_carrier="FX",
                flight_number="100",
                origin=query.origin,
                destination=query.destination,
                depart_at=depart_at,
                arrive_at=arrive_at,
                ordinal=0,
            ),
        )

        offers = []
        for seller_index, (seller, basic_economy) in enumerate(
            [("Fixture Airline Direct", False), ("Fixture OTA", query.include_basic_economy)]
        ):
            if basic_economy and not query.include_basic_economy:
                continue
            price = Money(self._deterministic_price(query, seller_index), query.display_currency)
            offers.append(
                Offer(
                    quote_id=f"fake-{query.origin}-{query.destination}-{query.departure_date}-{seller_index}",
                    itinerary_id="",  # filled in by caller after itinerary identity is built
                    provider_id=self.provider_id,
                    seller=f"{seller} ({SYNTHETIC_LABEL})",
                    fare_family="basic" if basic_economy else "standard",
                    cabin="economy",
                    basic_economy=basic_economy,
                    amount_original=price,
                    comparable_amount=price,
                    comparison_status=ComparisonStatus.ELIGIBLE_TOTAL_KNOWN,
                    checked_bag=ThreeValued.NO if basic_economy else ThreeValued.YES,
                    hidden_city=ThreeValued.NO,
                    self_transfer=ThreeValued.NO,
                    price_status=PriceStatus.RECENT_SEARCH,
                    is_estimate=False,
                    retrieved_at=retrieved_at,
                    repriced_at=None,
                    link=f"https://example.invalid/synthetic-offer/{seller_index}",
                    link_scope=LinkScope.GENERIC_SEARCH,
                    provider_quote_handle=f"fake-handle-{seller_index}",
                )
            )

        return ProviderSearchResult(
            provider_id=self.provider_id,
            requested=query,
            status=WorkStatus.SUCCEEDED_RESULTS,
            retrieved_at=retrieved_at,
            provider_complete=True,
            error_code=None,
            error_detail_sanitized=None,
            itineraries=(segments,),
            offers_by_itinerary_index=(tuple(offers),),
        )
