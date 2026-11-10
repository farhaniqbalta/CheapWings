"""Pinned swoop 0.7 adapter: bounded blocking I/O and conservative seller evidence."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from cheapwings.domain.coverage import WorkStatus
from cheapwings.domain.evidence import ProviderFailure, SourceEvidence
from cheapwings.domain.itinerary import ItinerarySummary, airport_transfers, compute_fingerprint
from cheapwings.domain.offer import ComparisonStatus, LinkScope, Offer, PriceStatus, ThreeValued
from cheapwings.domain.segments import FlightSegment
from cheapwings.providers.base import (
    ProviderCapabilities,
    ProviderRepriceResult,
    ProviderSearchResult,
)
from cheapwings.providers.common import json_payload, money, obj_dict, stable_id


class BoundedCall:
    """One actual thread slot, retained after await timeout/cancellation; no unbounded queue."""

    def __init__(self):
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="cheapwings-provider")
        self.future = None

    async def run(self, function, *args):
        if self.future is not None and not self.future.done():
            raise ProviderFailure("provider_unavailable")
        self.future = self.pool.submit(function, *args)
        return await asyncio.shield(asyncio.wrap_future(self.future))

    def close(self):
        self.pool.shutdown(wait=False, cancel_futures=True)


def airport_zone(code):
    airports = _airports()
    try:
        return airports[code]["tz"]
    except KeyError:
        raise ProviderFailure("missing_segments") from None


def _airports():
    # Assigned cached loader below to keep airport reference optional in fake mode.
    import airportsdata

    return airportsdata.load("IATA")


from functools import lru_cache

_airports = lru_cache(maxsize=1)(_airports)


def local_instant(date_parts, time_parts, code, resolver):
    naive = datetime(*date_parts, *time_parts)
    zone = ZoneInfo(resolver(code))
    a, b = naive.replace(tzinfo=zone, fold=0), naive.replace(tzinfo=zone, fold=1)
    if a.utcoffset() != b.utcoffset():
        raise ProviderFailure("missing_segments")  # ambiguous or nonexistent DST time
    if a.astimezone(UTC).astimezone(zone).replace(tzinfo=None) != naive:
        raise ProviderFailure("missing_segments")
    return a


class SwoopProvider:
    provider_id = "swoop"
    capabilities = ProviderCapabilities(True, False, True, True, False, False)

    def __init__(self, search_transport=None, price_transport=None, zone_resolver=None):
        self.search_transport = search_transport
        self.price_transport = price_transport
        self.zone_resolver = zone_resolver or airport_zone
        self.blocking = BoundedCall()

    @staticmethod
    def country(query):
        return (
            query.point_of_sale_country
            or {"IDR": "ID", "USD": "US", "AUD": "AU", "JPY": "JP"}[query.display_currency]
        )

    def _invoke(self, operation, value, country):
        import swoop

        transport = swoop.TransportConfig(timeout=20, retries=0, country=country)
        try:
            if operation == "search":
                q = value
                result = swoop.search(
                    q.origin,
                    q.destination,
                    str(q.departure_date),
                    cabin="economy",
                    include_basic_economy=q.include_basic_economy,
                    transport=transport,
                    time_budget=25,
                )
            else:
                result = swoop.price_selector(value, transport=transport)
            return obj_dict(result)
        except swoop.SwoopRateLimitError:
            raise ProviderFailure("http_rate_limited", 120) from None
        except swoop.SwoopHTTPError as exc:
            raise ProviderFailure(
                "auth_denied" if exc.status_code in (401, 403) else "provider_unavailable"
            ) from None
        except swoop.SwoopParseError:
            raise ProviderFailure("schema_changed") from None
        except swoop.SwoopUpstreamError as exc:
            raise ProviderFailure(
                "http_rate_limited"
                if exc.grpc_code == 8
                else "auth_denied"
                if exc.grpc_code in (7, 16)
                else "provider_unavailable",
                120 if exc.grpc_code == 8 else 0,
            ) from None

    def segments(self, itinerary):
        result = []
        for i, s in enumerate(itinerary["segments"]):
            carrier = s["airline"]
            operator = s.get("operator") or carrier  # SDK empty operator means same carrier
            if not carrier or not s["flight_number"] or len(operator) not in (2, 3):
                raise ProviderFailure("missing_segments")
            result.append(
                FlightSegment(
                    carrier,
                    operator,
                    s["flight_number"],
                    s["departure_airport_code"],
                    s["arrival_airport_code"],
                    local_instant(
                        s["departure_date"],
                        s["departure_time"],
                        s["departure_airport_code"],
                        self.zone_resolver,
                    ),
                    local_instant(
                        s["arrival_date"],
                        s["arrival_time"],
                        s["arrival_airport_code"],
                        self.zone_resolver,
                    ),
                    i,
                    marketing_carrier_name=s.get("airline_name") or None,
                    operating_carrier_name=(s.get("airline_name") or None)
                    if operator == carrier
                    else None,
                )
            )
        if not result:
            raise ProviderFailure("missing_segments")
        return tuple(result)

    @staticmethod
    def summary(itinerary):
        return ItinerarySummary(
            itinerary["departure_airport_code"],
            itinerary["arrival_airport_code"],
            datetime(*itinerary["departure_date"], *itinerary["departure_time"]),
            datetime(*itinerary["arrival_date"], *itinerary["arrival_time"]),
            itinerary["travel_time"],
            itinerary["stop_count"],
            ("Segment identity or timezone unresolved; local times have no confirmed offset.",),
            carrier_names=tuple(
                name
                for name in itinerary.get("airline_names", [])
                if isinstance(name, str) and name.strip()
            ),
        )

    async def search(self, query):
        payload = (
            await self.search_transport(query)
            if self.search_transport
            else await self.blocking.run(self._invoke, "search", query, self.country(query))
        )
        try:
            return self.normalize_search(payload, query)
        except (KeyError, TypeError, ValueError, IndexError):
            raise ProviderFailure("schema_changed") from None

    def normalize_search(self, payload, query):
        now = datetime.now(UTC)
        itineraries, offers, summaries = [], [], []
        unpriced = 0
        transfers = []
        for trip in payload["results"]:
            if trip.get("price") is None:
                unpriced += 1
                continue
            if len(trip["legs"]) != 1:
                raise ProviderFailure("schema_changed")
            leg = trip["legs"][0]
            if (leg["origin"], leg["destination"], leg["date"]) != (
                query.origin,
                query.destination,
                str(query.departure_date),
            ):
                raise ProviderFailure("schema_changed")
            itinerary = leg["itinerary"]
            try:
                segments, summary = self.segments(itinerary), None
            except (ProviderFailure, KeyError):
                segments, summary = (), self.summary(itinerary)
            original = money(trip["price"], trip["currency"])
            import json

            selector = trip.get("selector")
            handle = (
                json.dumps({"selector": selector, "country": self.country(query)})
                if selector
                else None
            )
            offer = Offer(
                stable_id(selector, itinerary),
                "",
                self.provider_id,
                None,
                None,
                "economy",
                None,
                original,
                original if original.currency == query.display_currency else None,
                ComparisonStatus.EXTRA_COST_UNKNOWN
                if original.currency == query.display_currency
                else ComparisonStatus.CURRENCY_UNRESOLVED,
                ThreeValued.UNKNOWN,
                ThreeValued.UNKNOWN,
                ThreeValued.UNKNOWN,
                PriceStatus.RECENT_SEARCH,
                False,
                now,
                None,
                None,
                LinkScope.UNAVAILABLE,
                handle,
                (
                    "Seller/fare/baggage/mandatory-fee details unavailable from search.",
                    "Hidden-city risk unknown; excluded from safe ranking.",
                ),
                SourceEvidence(
                    point_of_sale_country=self.country(query),
                    attribution="Google Flights via swoop",
                ),
            )
            itineraries.append(segments)
            summaries.append(summary)
            changes = airport_transfers(segments)
            if changes:
                offer = replace(
                    offer,
                    warnings=offer.warnings
                    + tuple(
                        f"Airport change required: {change.from_airport} → {change.to_airport}; ground transport costs and connection protection are unconfirmed."
                        for change in changes
                    ),
                )
            transfers.append(changes)
            offers.append((offer,))
        complete = payload.get("is_complete")
        if type(complete) is not bool:
            raise ProviderFailure("schema_changed")
        return ProviderSearchResult(
            self.provider_id,
            query,
            WorkStatus.SUCCEEDED_RESULTS if offers else WorkStatus.SUCCEEDED_EMPTY,
            now,
            complete,
            None,
            None,
            tuple(itineraries),
            tuple(offers),
            tuple(summaries),
            unpriced,
            tuple(transfers),
        )

    async def reprice(self, request):
        handle = json_payload(request.offer.provider_quote_handle)
        selector, country = handle["selector"], handle["country"]
        payload = (
            await self.price_transport(selector)
            if self.price_transport
            else await self.blocking.run(self._invoke, "price", selector, country)
        )
        if payload is None:
            return ProviderRepriceResult((), (), False, False)
        try:
            segments = self.segments(payload["itinerary"])
            if compute_fingerprint(segments) != compute_fingerprint(request.segments):
                return ProviderRepriceResult((), segments, True, False, ("Itinerary changed.",))
            estimate = payload["is_estimate"]
            if type(estimate) is not bool:
                raise ProviderFailure("schema_changed")
            offers = []
            for option in payload["booking_options"]:
                original = money(option["price"], payload["currency"])
                now = datetime.now(UTC)
                seller, family, basic = (
                    option.get("seller_name"),
                    option.get("fare_family"),
                    option.get("is_basic"),
                )
                # Each booking option is its own seller/fare, never the top-level basic flag.
                offers.append(
                    replace(
                        request.offer,
                        quote_id=stable_id(
                            selector, seller, family, basic, option.get("brand_code")
                        ),
                        seller=seller,
                        fare_family=family,
                        basic_economy=basic,
                        amount_original=original,
                        comparable_amount=original
                        if original.currency == request.query.display_currency
                        else None,
                        price_status=PriceStatus.INDICATIVE
                        if estimate
                        else PriceStatus.RECENT_SEARCH,
                        is_estimate=estimate,
                        retrieved_at=now,
                        repriced_at=None,
                        link=None,
                        link_scope=LinkScope.UNAVAILABLE,
                        warnings=(
                            "Seller option checked; hidden-city risk, baggage and fees remain unknown.",
                        ),
                        evidence=SourceEvidence(
                            point_of_sale_country=country, attribution="Google Flights via swoop"
                        ),
                    )
                )
            # Swoop cannot assert hidden-city=no; exact badge forbidden even on non-estimate.
            return ProviderRepriceResult(tuple(offers), segments, True, False)
        except (KeyError, TypeError, ValueError, IndexError):
            raise ProviderFailure("schema_changed") from None
