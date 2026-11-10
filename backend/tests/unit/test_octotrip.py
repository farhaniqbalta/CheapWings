"""Synthetic OctoTrip-shaped data: no real fare or signed booking link."""

import json
from datetime import date
from decimal import Decimal

import httpx
import pytest

from cheapwings.domain.evidence import ProviderFailure
from cheapwings.providers.base import SingleDateRouteQuery
from cheapwings.providers.octotrip import OctotripProvider


def query(**changes):
    return SingleDateRouteQuery(
        **dict(
            origin="CGK",
            destination="DPS",
            departure_date=date(2026, 12, 15),
            include_basic_economy=True,
            include_hidden_city=False,
            display_currency="USD",
            **changes,
        )
    )


def payload():
    return {
        "origin_resolved": {"iata": "CGK"},
        "destination_resolved": {"iata": "DPS"},
        "query": {"departure_date": "2026-12-15"},
        "total": 1,
        "total_available": 100,
        "results": [
            {
                "airline": "SYNTHETIC AIRLINE",
                "gate": "SYNTHETIC SELLER",
                "price": Decimal("123.45"),
                "currency": "USD",
                "baggage": "No checked bag, Cabin bag: 1 piece(s)",
                "booking_url": "https://mcp.octotrip.app/synthetic-not-a-real-offer",
                "outbound": {
                    "departure": "CGK",
                    "arrival": "DPS",
                    "departure_date": "2026-12-15",
                    "arrival_date": "2026-12-15",
                    "departure_time": "10:00",
                    "arrival_time": "12:50",
                    "duration_minutes": 110,
                    "stops": 0,
                    "legs": [{"flight_number": "XX123"}],
                },
            }
        ],
    }


def test_summary_is_honest_and_money_and_source_metadata_retained():
    result = OctotripProvider().normalize(payload(), query())
    assert result.itinerary_summaries[0].duration_minutes == 110
    assert result.itinerary_summaries[0].depart_at.utcoffset().total_seconds() == 7 * 3600
    assert result.provider_complete is False
    assert result.itineraries == ((),)
    assert result.itinerary_summaries[0].carrier_names == ("SYNTHETIC AIRLINE",)
    assert "XX123" in result.itinerary_summaries[0].warnings[-1]
    offer = result.offers_by_itinerary_index[0][0]
    assert offer.amount_original.amount == Decimal("123.45")
    assert offer.seller == "SYNTHETIC SELLER"
    assert offer.hidden_city.value == offer.self_transfer.value == "unknown"
    assert offer.checked_bag.value == "no"
    assert offer.price_status.value == "indicative" and offer.is_estimate
    assert offer.link_scope.value == "itinerary"
    assert offer.provider_quote_handle is None
    assert offer.evidence.source_checked_at is None


@pytest.mark.parametrize("kind", ["float", "route", "date", "link"])
def test_bad_source_values_fail_or_disable_navigation(kind):
    data = payload()
    if kind == "float":
        data["results"][0]["price"] = 123.45
    if kind == "route":
        data["origin_resolved"]["iata"] = "JKT"
    if kind == "date":
        data["query"]["departure_date"] = "2026-12-16"
    if kind == "link":
        data["results"][0]["booking_url"] = "https://evil.example/signed-token"
    if kind == "link":
        assert (
            OctotripProvider().normalize(data, query()).offers_by_itinerary_index[0][0].link is None
        )
    else:
        with pytest.raises(ProviderFailure):
            OctotripProvider().normalize(data, query())


async def test_unsupported_filters_do_not_call_transport():
    calls = []

    async def transport(request):
        calls.append(request)
        return payload()

    p = OctotripProvider(transport)
    q = SingleDateRouteQuery("CGK", "DPS", date(2026, 12, 15), False, False, "USD")
    with pytest.raises(ProviderFailure, match="unsupported_query"):
        await p.search(q)
    assert calls == []


async def test_rpc_sse_decimal_decode_and_429():
    seen = []

    async def handler(request):
        seen.append(json.loads(request.content))
        return httpx.Response(
            200,
            headers={"Content-Type": "text/event-stream"},
            text='event: message\ndata: {"jsonrpc":"2.0","id":2,"result":{"amount":123.45}}\n\n',
        )

    p = OctotripProvider()
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await p._rpc(client, 2, "tools/call", {"name": "search"})
    assert result["amount"] == Decimal("123.45") and isinstance(result["amount"], Decimal)

    async def limited(request):
        return httpx.Response(429, headers={"Retry-After": "120"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(limited)) as client:
        with pytest.raises(ProviderFailure) as exc:
            await p._rpc(client, 2, "tools/call", {})
        assert exc.value.code == "http_rate_limited" and exc.value.retry_after_seconds == 120


def test_neighbor_airports_are_excluded_and_elapsed_time_includes_layover():
    from copy import deepcopy

    data = payload()
    neighbor = deepcopy(data["results"][0])
    neighbor["outbound"]["departure"] = "HLP"
    data["results"].append(neighbor)
    data["results"][0]["outbound"].update(arrival_time="20:00", duration_minutes=110, stops=1)
    result = OctotripProvider().normalize(data, query())
    assert len(result.itineraries) == 1
    assert result.itinerary_summaries[0].duration_minutes == 540
    assert "Excluded 1" in result.offers_by_itinerary_index[0][0].warnings[-1]
    data["results"] = [neighbor]
    with pytest.raises(ProviderFailure) as error:
        OctotripProvider().normalize(data, query())
    assert error.value.code == "partial_payload"
