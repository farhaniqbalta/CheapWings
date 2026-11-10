"""Skiplagged MCP adapter pinned to P0 FlightCard evidence, never invented legs."""

from datetime import UTC, datetime
from urllib.parse import urlsplit

from cheapwings.domain.coverage import WorkStatus
from cheapwings.domain.evidence import ProviderFailure, SourceEvidence
from cheapwings.domain.itinerary import ItinerarySummary
from cheapwings.domain.money import FXSnapshot
from cheapwings.domain.offer import ComparisonStatus, LinkScope, Offer, PriceStatus, ThreeValued
from cheapwings.providers.base import ProviderCapabilities, ProviderSearchResult
from cheapwings.providers.common import aware_iso, decimal_value, json_payload, money, stable_id

ENDPOINT = "https://mcp.skiplagged.com/mcp"


async def mcp_search(arguments):
    import httpx2 as httpx
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    from cheapwings.providers.exact_json import ExactCapture, exact_http_client

    capture = ExactCapture()
    async with exact_http_client(capture) as client:
        try:
            async with streamable_http_client(ENDPOINT, http_client=client) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool("sk_flights_search", arguments)
                    if result.is_error:
                        raise ProviderFailure("provider_unavailable")
                    if capture.result is not None:
                        return capture.result
                    # Prefer raw JSON text to avoid binary floats in structured_content.
                    for block in result.content:
                        if getattr(block, "type", None) == "text":
                            try:
                                payload = json_payload(block.text)
                            except ValueError:
                                continue
                            if isinstance(payload, dict) and "flights" in payload:
                                return payload
                    # Some MCP servers wrap the tool JSON in structured_content.
                    # Integer-only structured prices are safe; floats fail closed in normalization.
                    if result.structured_content is not None:
                        return result.structured_content
                    raise ProviderFailure("schema_changed")
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            retry = exc.response.headers.get("Retry-After", "0")
            raise ProviderFailure(
                "http_rate_limited"
                if status == 429
                else "auth_denied"
                if status in (401, 403)
                else "provider_unavailable",
                int(retry) if retry.isdigit() else 0,
            ) from None


class SkiplaggedProvider:
    provider_id = "skiplagged"
    # Calendar tools exist, but no implemented/tested calendar method is advertised.
    capabilities = ProviderCapabilities(True, False, False, True, True, False)

    def __init__(self, transport=None, limit=20):
        self.transport = transport or mcp_search
        self.limit = limit

    async def search(self, query):
        if not query.include_basic_economy:
            raise ProviderFailure("unsupported_query")  # no observed basic-economy filter
        if query.point_of_sale_country:
            raise ProviderFailure("unsupported_query")  # no observed POS control
        args = dict(
            origin=query.origin,
            destination=query.destination,
            departureDate=str(query.departure_date),
            adults=1,
            fareClass="economy",
            limit=self.limit,
            includeHiddenCity=False,
            includeVirtualInterlining=False,
            currency=query.display_currency,
        )
        payload = await self.transport(args)
        try:
            return self.normalize(payload, query)
        except (KeyError, TypeError, ValueError, IndexError):
            raise ProviderFailure("schema_changed") from None

    def normalize(self, payload, query):
        now = datetime.now(UTC)
        cards = payload["flights"]
        if not isinstance(cards, list):
            raise ProviderFailure("schema_changed")
        pricing = payload.get("pricing", {})
        itineraries, offers, summaries = [], [], []
        for card in cards:
            depart = aware_iso(card["departure"]["dateTime"])
            arrive = aware_iso(card["arrival"]["dateTime"])
            if (
                card["departure"]["airport"] != query.origin
                or card["arrival"]["airport"] != query.destination
                or depart.date() != query.departure_date
            ):
                raise ProviderFailure("schema_changed")
            original = money(card["price"]["usdAmount"], "USD")
            fx = None
            if query.display_currency == "USD":
                compared = original
            elif pricing.get("currency") == query.display_currency and pricing.get("rateAsOf"):
                fx = FXSnapshot(
                    "USD",
                    query.display_currency,
                    decimal_value(pricing["rate"]),
                    "provider_quote_display_only",
                    pricing["rateAsOf"],
                )
                compared = fx.convert(original)
            else:
                compared = None
            # No per-segment operating carrier exists, including nonstop cards. Preserve
            # observed route/times/stops as summary, never force a cross-source fingerprint.
            stops = card["layovers"]
            if type(stops) is not int or stops < 0:
                raise ProviderFailure("schema_changed")
            duration = int((arrive - depart).total_seconds() // 60)
            summary = ItinerarySummary(
                query.origin,
                query.destination,
                depart,
                arrive,
                duration,
                stops,
                ("Full segment identity unavailable.",),
                carrier_names=(card["airlines"].strip(),)
                if isinstance(card.get("airlines"), str) and card["airlines"].strip()
                else (),
            )
            link = card.get("deepLink")
            parsed = urlsplit(link or "")
            if parsed.scheme != "https" or parsed.hostname != "skiplagged.com":
                link = None
            offer = Offer(
                quote_id=stable_id(card["id"]),
                itinerary_id="",
                provider_id=self.provider_id,
                seller=None,
                fare_family=None,
                cabin="economy",
                basic_economy=None,
                amount_original=original,
                comparable_amount=compared,
                comparison_status=ComparisonStatus.EXTRA_COST_UNKNOWN
                if compared
                else ComparisonStatus.CURRENCY_UNRESOLVED,
                checked_bag=ThreeValued.UNKNOWN,
                hidden_city=ThreeValued.NO,
                self_transfer=ThreeValued.NO,
                price_status=PriceStatus.INDICATIVE,
                is_estimate=True,
                retrieved_at=now,
                repriced_at=None,
                link=link,
                link_scope=LinkScope.GENERIC_SEARCH if link else LinkScope.UNAVAILABLE,
                provider_quote_handle=None,
                warnings=(
                    "Source price is indicative; seller, fees, fare and baggage are unknown.",
                    "Hidden-city and virtual interlining excluded by upstream request.",
                ),
                evidence=SourceEvidence(fx_snapshot=fx, attribution="Skiplagged"),
            )
            itineraries.append(())
            summaries.append(summary)
            offers.append((offer,))
        pagination = payload.get("pagination", {})
        complete = (
            not pagination["hasMoreResults"]
            if type(pagination.get("hasMoreResults")) is bool
            else None
        )
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
        )
