"""OctoTrip stateless MCP v1.30: advertised prices, never exact fare confirmation."""

import asyncio
import codecs
from dataclasses import replace
from datetime import UTC, datetime
from urllib.parse import urlsplit

import httpx

from cheapwings.domain.coverage import WorkStatus
from cheapwings.domain.evidence import ProviderFailure, SourceEvidence
from cheapwings.domain.itinerary import ItinerarySummary
from cheapwings.domain.offer import ComparisonStatus, LinkScope, Offer, PriceStatus, ThreeValued
from cheapwings.providers.base import ProviderCapabilities, ProviderSearchResult
from cheapwings.providers.common import json_payload, money, stable_id
from cheapwings.providers.swoop import airport_zone, local_instant

ENDPOINT = "https://mcp.octotrip.app/flights/mcp"


class OctotripProvider:
    provider_id = "octotrip"
    capabilities = ProviderCapabilities(True, False, False, True, False, False)

    def __init__(self, transport=None):
        self.transport = transport

    async def _rpc(self, client, ident, method, params):
        async with client.stream(
            "POST",
            ENDPOINT,
            json={
                "jsonrpc": "2.0",
                "id": ident,
                "method": method,
                "params": params,
            },
        ) as response:
            if response.status_code == 429:
                try:
                    retry = max(15, int(response.headers.get("Retry-After", "60")))
                except ValueError:
                    retry = 60
                raise ProviderFailure("http_rate_limited", retry)
            if response.status_code in (401, 403):
                raise ProviderFailure("auth_denied")
            if response.status_code != 200:
                raise ProviderFailure("provider_unavailable")
            chunks, size = [], 0
            event_stream = "text/event-stream" in response.headers.get("Content-Type", "")
            decoder = codecs.getincrementaldecoder("utf-8")()
            buffer = ""
            async for chunk in response.aiter_bytes():
                size += len(chunk)
                if size > 2_000_000:
                    raise ProviderFailure("partial_payload")
                if event_stream:
                    buffer = (buffer + decoder.decode(chunk)).replace("\r\n", "\n")
                    frames = buffer.split("\n\n")
                    buffer = frames.pop()
                    for frame in frames:
                        data = "\n".join(
                            line[5:].lstrip(" ")
                            for line in frame.splitlines()
                            if line.startswith("data:")
                        )
                        if data:
                            envelope = json_payload(data)
                            if envelope.get("id") == ident:
                                return self.rpc_result(envelope)
                else:
                    chunks.append(chunk)
            if event_stream:
                raise ProviderFailure("partial_payload")
            return self.rpc_result(json_payload(b"".join(chunks).decode()))

    @staticmethod
    def rpc_result(envelope):
        if not isinstance(envelope, dict) or envelope.get("error"):
            raise ProviderFailure("provider_unavailable")
        result = envelope["result"]
        if not isinstance(result, dict):
            raise ProviderFailure("schema_changed")
        if result.get("isError"):
            raise ProviderFailure("provider_unavailable")
        return result

    async def fetch(self, query):
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(60, connect=5),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "User-Agent": "CheapWings-Personal/0.1",
            },
        ) as client:
            await self._rpc(
                client,
                1,
                "initialize",
                {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "cheapwings", "version": "0.1"},
                },
            )
            await asyncio.sleep(1.05)  # published 1 request/second includes MCP requests
            result = await self._rpc(
                client,
                2,
                "tools/call",
                {
                    "name": "search",
                    "arguments": {
                        "origin": query.origin,
                        "destination": query.destination,
                        "departure_date": str(query.departure_date),
                        "adults": 1,
                        "children": 0,
                        "infants": 0,
                        "trip_class": "Y",
                        "currency": query.display_currency,
                        "locale": "en",
                    },
                },
            )
        payload = result.get("structuredContent")
        if payload is None:
            payload = next(c["text"] for c in result.get("content", []) if c.get("type") == "text")
        for _ in range(5):
            if isinstance(payload, str):
                payload = json_payload(payload)
            elif isinstance(payload, dict) and "results" not in payload and "result" in payload:
                payload = payload["result"]
            else:
                break
        return payload

    async def search(self, query):
        # Unsupported controls are rejected, never silently ignored or substituted.
        if not query.include_basic_economy or query.point_of_sale_country:
            raise ProviderFailure("unsupported_query")
        try:
            payload = await self.transport(query) if self.transport else await self.fetch(query)
            return self.normalize(payload, query)
        except httpx.TimeoutException:
            raise ProviderFailure("network_timeout") from None
        except httpx.HTTPError:
            raise ProviderFailure("provider_unavailable") from None
        except (KeyError, ValueError, TypeError, IndexError, StopIteration):
            raise ProviderFailure("schema_changed") from None

    def normalize(self, payload, query):
        if payload.get("error"):
            raise ProviderFailure(
                "unsupported_query"
                if payload["error"]
                in ("airport_not_found", "invalid_date", "disambiguation_needed")
                else "provider_unavailable"
            )
        if (payload["origin_resolved"]["iata"], payload["destination_resolved"]["iata"]) != (
            query.origin,
            query.destination,
        ):
            raise ProviderFailure("schema_changed")
        if payload["query"]["departure_date"] != str(query.departure_date):
            raise ProviderFailure("schema_changed")
        rows = payload["results"]
        if not isinstance(rows, list):
            raise ProviderFailure("schema_changed")
        now = datetime.now(UTC)
        summaries, offers = [], []
        excluded = 0
        for row in rows:
            outbound = row["outbound"]
            if (outbound["departure"], outbound["arrival"], outbound["departure_date"]) != (
                query.origin,
                query.destination,
                str(query.departure_date),
            ) or row.get("return"):
                excluded += 1
                continue
            depart = datetime.fromisoformat(
                f"{outbound['departure_date']}T{outbound['departure_time']}"
            )
            arrive = datetime.fromisoformat(
                f"{outbound['arrival_date']}T{outbound['arrival_time']}"
            )
            depart = local_instant(
                [depart.year, depart.month, depart.day],
                [depart.hour, depart.minute],
                query.origin,
                airport_zone,
            )
            arrive = local_instant(
                [arrive.year, arrive.month, arrive.day],
                [arrive.hour, arrive.minute],
                query.destination,
                airport_zone,
            )
            elapsed = int((arrive.astimezone(UTC) - depart.astimezone(UTC)).total_seconds() // 60)
            # Endpoint offsets are reference-validated; full operating/segment identity is unknown.
            source_flights = tuple(
                str(l["flight_number"]) for l in outbound.get("legs", []) if l.get("flight_number")
            )
            summary_warnings = (
                "OctoTrip routing summary; full segment identity and operating carriers unconfirmed.",
            )
            if source_flights:
                summary_warnings += (
                    "Source-reported flight numbers: " + ", ".join(source_flights),
                )
            summary = ItinerarySummary(
                query.origin,
                query.destination,
                depart,
                arrive,
                elapsed,
                int(outbound["stops"]),
                summary_warnings,
                carrier_names=(row["airline"],) if row.get("airline") else (),
            )
            if summary.duration_minutes < 0 or summary.stops < 0:
                raise ProviderFailure("schema_changed")
            amount = money(row["price"], row["currency"])
            link = row.get("booking_url")
            parsed = urlsplit(link or "")
            if (
                parsed.scheme != "https"
                or parsed.hostname != "mcp.octotrip.app"
                or parsed.username
                or parsed.password
            ):
                link = None
            baggage = row.get("baggage")
            warnings = [
                "Limited price-ranked source shortlist; not complete flight inventory.",
                "Source observation time, mandatory fees, fare product and hidden-city/self-transfer risk unconfirmed.",
                "Affiliate booking link; OctoTrip may earn a commission. Final seller price must be checked.",
            ]
            if isinstance(baggage, str) and baggage:
                warnings.append(
                    "Source baggage statement (not independently checked): " + baggage[:500]
                )
            summaries.append(summary)
            offers.append(
                (
                    Offer(
                        stable_id(row),
                        "",
                        self.provider_id,
                        row.get("gate") or None,
                        None,
                        "economy",
                        None,
                        amount,
                        amount if amount.currency == query.display_currency else None,
                        ComparisonStatus.EXTRA_COST_UNKNOWN
                        if amount.currency == query.display_currency
                        else ComparisonStatus.CURRENCY_UNRESOLVED,
                        ThreeValued.NO
                        if isinstance(baggage, str) and baggage.lower().startswith("no checked bag")
                        else ThreeValued.UNKNOWN,
                        ThreeValued.UNKNOWN,
                        ThreeValued.UNKNOWN,
                        PriceStatus.INDICATIVE,
                        True,
                        now,
                        None,
                        link,
                        LinkScope.ITINERARY if link else LinkScope.UNAVAILABLE,
                        None,
                        tuple(warnings),
                        SourceEvidence(attribution="OctoTrip · affiliate links"),
                    ),
                )
            )
        if excluded:
            if not offers:
                raise ProviderFailure("partial_payload")
            note = (
                f"Excluded {excluded} source candidates outside the requested exact airports/date."
            )
            offers = [
                tuple(replace(o, warnings=o.warnings + (note,)) for o in group) for group in offers
            ]
        return ProviderSearchResult(
            self.provider_id,
            query,
            WorkStatus.SUCCEEDED_RESULTS if offers else WorkStatus.SUCCEEDED_EMPTY,
            now,
            False,
            None,
            None,
            tuple(() for _ in summaries),
            tuple(offers),
            tuple(summaries),
        )
