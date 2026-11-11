"""Fli public-page adapter: bounded blocking I/O, exact prices, no fare verification.

Pinned Fli builders/row decoder are used without global patches. Its generic
retry/client layer is replaced by one synchronous request path so the durable
worker owns retries and physical capacity until the network call truly ends.
"""

import copy
import logging
import re
import threading
from datetime import UTC, datetime
from time import monotonic
from typing import ClassVar
from urllib.parse import urljoin, urlsplit

from cheapwings.domain.coverage import WorkStatus
from cheapwings.domain.evidence import ProviderFailure, SourceEvidence
from cheapwings.domain.itinerary import airport_transfers
from cheapwings.domain.offer import ComparisonStatus, LinkScope, Offer, PriceStatus, ThreeValued
from cheapwings.domain.segments import FlightSegment
from cheapwings.providers.base import ProviderCapabilities, ProviderSearchResult
from cheapwings.providers.common import json_payload, money, stable_id
from cheapwings.providers.rate_limit import retry_after
from cheapwings.providers.swoop import BoundedCall, airport_zone, local_instant

logger = logging.getLogger(__name__)


class FliProvider:
    provider_id = "fli"
    capabilities = ProviderCapabilities(True, False, False, True, False, False)
    cache_dependencies = ("flights", "airportsdata")
    cache_version = "1"
    cache_options: ClassVar[dict] = {"transport": "public_page", "stops": "any", "cabin": "economy"}

    def __init__(self, transport=None, *, concurrency=3, zone_resolver=None):
        self.transport = transport
        self.blocking = BoundedCall(concurrency)
        self.zone_resolver = zone_resolver or airport_zone
        self._lock = threading.Lock()
        self._next_http = 0.0
        self._blocked = False

    def _check_feedback(self):
        with self._lock:
            if self._blocked:
                raise ProviderFailure("auth_denied")
            remaining = self._next_http - monotonic()
            if remaining > 0:
                raise ProviderFailure("http_rate_limited", remaining)

    def _deny(self):
        with self._lock:
            self._blocked = True
        raise ProviderFailure("auth_denied")

    def _get(self, session, url):
        for _ in range(3):
            self._check_feedback()
            response = session.get(url, timeout=25, impersonate="chrome", allow_redirects=False)
            status = response.status_code
            logger.info("fli_http_response status=%d", status)
            if status == 429:
                delay = retry_after(response.headers.get("Retry-After"), default=120)
                with self._lock:
                    self._next_http = max(self._next_http, monotonic() + delay)
                raise ProviderFailure("http_rate_limited", delay)
            if status in (401, 403):
                self._deny()
            if status in (301, 302, 303, 307, 308):
                target = urljoin(url, response.headers.get("location", ""))
                parsed = urlsplit(target)
                if (
                    parsed.scheme != "https"
                    or parsed.hostname != "www.google.com"
                    or not parsed.path.startswith("/travel/flights")
                    or parsed.path.endswith("/unsupported")
                ):
                    self._deny()
                url = target
                continue
            if status != 200:
                raise ProviderFailure("provider_unavailable")
            if len(response.content) > 4_000_000:
                raise ProviderFailure("partial_payload")
            html = response.text
            if any(
                marker in html.lower()
                for marker in (
                    "our systems have detected unusual traffic",
                    "unusual traffic from your computer",
                )
            ):
                self._deny()
            return html, url
        raise ProviderFailure("provider_unavailable")

    def _fetch(self, query):
        from curl_cffi import CurlHttpVersion
        from curl_cffi.requests import Session
        from curl_cffi.requests.exceptions import RequestException
        from fli.models import (
            Airport,
            FlightSearchFilters,
            MaxStops,
            PassengerInfo,
            SeatType,
            TripType,
        )
        from fli.models import FlightSegment as FliSegment
        from fli.search import _tfs

        try:
            origin, destination = Airport[query.origin], Airport[query.destination]
        except KeyError:
            raise ProviderFailure("unsupported_query") from None
        filters = FlightSearchFilters(
            trip_type=TripType.ONE_WAY,
            passenger_info=PassengerInfo(adults=1),
            flight_segments=[
                FliSegment(
                    departure_airport=[[origin, 0]],
                    arrival_airport=[[destination, 0]],
                    travel_date=str(query.departure_date),
                )
            ],
            seat_type=SeatType.ECONOMY,
            stops=MaxStops.ANY,
        )
        country = (
            query.point_of_sale_country
            or {
                "IDR": "ID",
                "USD": "US",
                "AUD": "AU",
                "JPY": "JP",
            }[query.display_currency]
        )
        url = _tfs.page_url(_tfs.build_tfs(filters), query.display_currency, "en", country)
        try:
            with Session(http_version=CurlHttpVersion.V2TLS) as session:
                html, final_url = self._get(session, url)
        except RequestException as exc:
            logger.warning("fli_http_transport_failed curl_code=%s", exc.code)
            failure = ProviderFailure(
                "network_timeout" if exc.code == 28 else "provider_unavailable"
            )
            failure.transport_code = exc.code  # Numeric diagnostics only; never raw exception text.
            raise failure from None
        # Fli's extraction pattern, but Decimal parsing preserves the original
        # numeric lexemes; do not use SDK float-valued FlightResult.price.
        for match in _tfs._DS_BLOB.finditer(html):
            blob = match.group(1)
            key = _tfs._DS_KEY.search(blob)
            if not key or key.group(1) != "ds:1":
                continue
            data = _tfs._DS_DATA.search(blob)
            if data:
                try:
                    return {"data": json_payload(data.group(1)), "url": final_url}
                except ValueError:
                    break
        raise ProviderFailure("schema_changed")

    async def search(self, query):
        if not query.include_basic_economy:
            raise ProviderFailure("unsupported_query")
        try:
            payload = (
                await self.transport(query)
                if self.transport
                else await self.blocking.run(self._fetch, query)
            )
            return self.normalize(payload, query)
        except (KeyError, ValueError, TypeError, IndexError, AttributeError):
            raise ProviderFailure("schema_changed") from None

    def _segments(self, flight):
        result = []
        for i, leg in enumerate(flight.legs):
            origin = leg.departure_airport.name.removeprefix("_")
            destination = leg.arrival_airport.name.removeprefix("_")
            carrier = leg.airline.name.removeprefix("_") if leg.airline else ""
            operator = (
                leg.operating_airline.name.removeprefix("_") if leg.operating_airline else carrier
            )
            if not re.fullmatch(r"[A-Z0-9]{2,3}", carrier) or not leg.flight_number:
                raise ProviderFailure("missing_segments")
            times = []
            for instant, airport in (
                (leg.departure_datetime, origin),
                (leg.arrival_datetime, destination),
            ):
                if instant.tzinfo is None:
                    instant = local_instant(
                        (instant.year, instant.month, instant.day),
                        (instant.hour, instant.minute),
                        airport,
                        self.zone_resolver,
                    )
                times.append(instant)
            if times[1].astimezone(UTC) <= times[0].astimezone(UTC):
                raise ProviderFailure("schema_changed")
            result.append(
                FlightSegment(
                    carrier,
                    operator,
                    leg.flight_number,
                    origin,
                    destination,
                    *times,
                    i,
                    marketing_carrier_name=leg.airline.value,
                    operating_carrier_name=(leg.operating_airline or leg.airline).value,
                )
            )
        return tuple(result)

    def normalize(self, payload, query):
        from fli.search._decoders import parse_flight_row

        data = payload["data"]
        if not isinstance(data, list) or len(data) < 4:
            raise ProviderFailure("schema_changed")
        rows = []
        saw_group = False
        for index in (2, 3):
            group = data[index]
            if group is None:
                continue
            if not isinstance(group, list) or not group or not isinstance(group[0], list):
                raise ProviderFailure("schema_changed")
            saw_group = True
            rows.extend(group[0])
        if len(rows) > 500:
            raise ProviderFailure("partial_payload")
        if not saw_group:
            raise ProviderFailure("schema_changed")
        now = datetime.now(UTC)
        itineraries, offers, transfers = [], [], []
        unpriced = 0
        for row in rows:
            head = row[1][0]
            if not isinstance(head, list):
                raise ProviderFailure("schema_changed")
            if not head:
                unpriced += 1
                continue
            amount = head[-1]
            # Decode identity/currency with the SDK, using a constant price
            # placeholder. The real monetary value never enters float math.
            identity_row = copy.deepcopy(row)
            identity_row[1][0][-1] = 0
            flight = parse_flight_row(identity_row)
            if flight.currency != query.display_currency:
                raise ProviderFailure("invalid_currency")
            original = money(amount, flight.currency)
            if original.amount <= 0:
                raise ProviderFailure("invalid_price")
            if (
                not flight.legs
                or flight.legs[0].departure_airport.name.removeprefix("_") != query.origin
                or flight.legs[-1].arrival_airport.name.removeprefix("_") != query.destination
            ):
                raise ProviderFailure("schema_changed")
            segments = self._segments(flight)
            if (
                not segments
                or segments[0].origin != query.origin
                or segments[-1].destination != query.destination
                or segments[0].depart_at.date() != query.departure_date
            ):
                raise ProviderFailure("schema_changed")
            link = payload.get("url")
            parsed = urlsplit(link or "")
            if (
                parsed.scheme != "https"
                or parsed.hostname != "www.google.com"
                or not parsed.path.startswith("/travel/flights")
                or parsed.username
                or parsed.password
            ):
                link = None
            offer = Offer(
                stable_id(self.provider_id, segments, original),
                "",
                self.provider_id,
                None,
                None,
                "economy",
                None,
                original,
                original,
                ComparisonStatus.EXTRA_COST_UNKNOWN,
                ThreeValued.UNKNOWN,
                ThreeValued.UNKNOWN,
                ThreeValued.UNKNOWN,
                PriceStatus.INDICATIVE,
                True,
                now,
                None,
                link,
                LinkScope.GENERIC_SEARCH if link else LinkScope.UNAVAILABLE,
                None,
                (
                    "Public-page shortlist; complete flight inventory is unknown.",
                    "Baggage, fees, hidden-city and self-transfer risk are unconfirmed.",
                    "Fli and swoop both use Google Flights; they are not independent inventories.",
                ),
                SourceEvidence(
                    source_checked_at=now,
                    attribution="Google Flights via Fli",
                    point_of_sale_country=query.point_of_sale_country
                    or {
                        "IDR": "ID",
                        "USD": "US",
                        "AUD": "AU",
                        "JPY": "JP",
                    }[query.display_currency],
                ),
            )
            itineraries.append(segments)
            offers.append((offer,))
            transfers.append(airport_transfers(segments))
        return ProviderSearchResult(
            self.provider_id,
            query,
            WorkStatus.SUCCEEDED_RESULTS if offers else WorkStatus.SUCCEEDED_EMPTY,
            now,
            bool(offers) and not unpriced,
            None,
            None,
            tuple(itineraries),
            tuple(offers),
            unpriced_candidate_count=unpriced,
            airport_transfers_by_itinerary_index=tuple(transfers),
        )

    async def reprice(self, request):
        raise ProviderFailure("unsupported_query")
