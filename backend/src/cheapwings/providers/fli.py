"""Fli public-page adapter: bounded blocking I/O, exact prices, no fare verification.

The pinned Fli SDK builds requests. Rust decodes result rows.
The synchronous request path lets the durable
worker owns retries and physical capacity until the network call truly ends.
"""

import logging
import re
import threading
from datetime import UTC, datetime
from functools import lru_cache
from importlib.resources import files
from time import monotonic
from typing import ClassVar
from urllib.parse import urljoin, urlsplit

from pydantic import PositiveInt

from cheapwings._core import core as _core
from cheapwings.domain.coverage import WorkStatus
from cheapwings.domain.evidence import ProviderFailure, SourceEvidence
from cheapwings.domain.itinerary import airport_transfers
from cheapwings.domain.offer import ComparisonStatus, LinkScope, Offer, PriceStatus, ThreeValued
from cheapwings.domain.segments import FlightSegment
from cheapwings.providers.base import ProviderCapabilities, ProviderSearchResult
from cheapwings.providers.common import exact_payload_json, json_payload, money, stable_id
from cheapwings.providers.rate_limit import retry_after
from cheapwings.providers.swoop import BoundedCall, airport_zone, local_instant
from cheapwings.typeadapters import adapter

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _codes():
    return json_payload(files(__package__).joinpath("fli_codes.json").read_text())


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
        try:
            return {"data": json_payload(_core.fli_extract_ds1(html)), "url": final_url}
        except ValueError:
            raise ProviderFailure("schema_changed") from None

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

    @staticmethod
    def _validated_legs(record):
        codes = _codes()
        legs = []
        for leg in record["legs"]:
            airline = codes["airlines"].get(leg["airline"])
            if airline is None:
                raise ProviderFailure("schema_changed")
            operator = codes["airlines"].get(leg["operator"], airline)
            adapter(PositiveInt).validate_python(leg["duration"])
            legs.append(
                (
                    codes["airports"][leg["origin"]],
                    codes["airports"][leg["destination"]],
                    airline,
                    operator,
                    leg["flight_number"],
                    datetime(*(value or 0 for value in leg["depart"])),
                    datetime(*(value or 0 for value in leg["arrive"])),
                )
            )
        adapter(PositiveInt).validate_python(record["duration"])
        return legs

    def _segments(self, legs):
        result = []
        for i, (origin, destination, airline, operator, flight, depart, arrive) in enumerate(legs):
            carrier, carrier_name = airline
            if not re.fullmatch(r"[A-Z0-9]{2,3}", carrier) or not flight:
                raise ProviderFailure("missing_segments")
            times = [
                local_instant(
                    (t.year, t.month, t.day), (t.hour, t.minute), airport, self.zone_resolver
                )
                if t.tzinfo is None
                else t
                for t, airport in ((depart, origin), (arrive, destination))
            ]
            if times[1].astimezone(UTC) <= times[0].astimezone(UTC):
                raise ProviderFailure("schema_changed")
            result.append(
                FlightSegment(
                    carrier,
                    operator[0],
                    flight,
                    origin,
                    destination,
                    *times,
                    i,
                    marketing_carrier_name=carrier_name,
                    operating_carrier_name=operator[1],
                )
            )
        return tuple(result)

    def normalize(self, payload, query):
        try:
            page = json_payload(_core.fli_parse(exact_payload_json(payload["data"])))
        except ValueError as exc:
            raise ProviderFailure(str(exc)) from None
        now = datetime.now(UTC)
        itineraries, offers, transfers = [], [], []
        unpriced = page["unpriced"]
        records = page["offers"]
        # A page with no offer in the display currency is a currency failure; a page that mixes
        # currencies keeps its comparable offers and counts the others (P7.7 live: one foreign
        # offer used to fail the whole route).
        present = [r for r in records if r is not None]
        if present and all(r["currency"] != query.display_currency for r in present):
            raise ProviderFailure("invalid_currency")
        for record in records:
            if record is None:
                raise ProviderFailure("schema_changed")
            legs = self._validated_legs(record)
            if record["currency"] != query.display_currency:
                unpriced += 1
                continue
            original = money(record["price"], record["currency"])
            if original.amount <= 0:
                raise ProviderFailure("invalid_price")
            if not legs or legs[0][0] != query.origin or legs[-1][1] != query.destination:
                raise ProviderFailure("schema_changed")
            segments = self._segments(legs)
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
