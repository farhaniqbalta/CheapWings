import asyncio
import threading
from datetime import date, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from cheapwings.domain.evidence import ProviderFailure
from cheapwings.providers.base import SingleDateRouteQuery
from cheapwings.providers.fli import FliProvider


def query():
    return SingleDateRouteQuery("HND", "CGK", date.today() + timedelta(days=20), True, False, "IDR")


@pytest.fixture
def decoder(monkeypatch):
    pytest.importorskip("fli")
    from fli.search import _decoders

    q = query()
    flight = SimpleNamespace(
        currency="IDR",
        legs=[
            SimpleNamespace(
                airline=SimpleNamespace(name="TR", value="Scoot"),
                operating_airline=None,
                flight_number="801",
                departure_airport=SimpleNamespace(name="HND"),
                arrival_airport=SimpleNamespace(name="CGK"),
                departure_datetime=datetime.combine(q.departure_date, datetime.min.time()).replace(
                    hour=9
                ),
                arrival_datetime=datetime.combine(q.departure_date, datetime.min.time()).replace(
                    hour=15
                ),
            )
        ],
    )

    def decode(row):
        assert row[1][0][-1] == 0  # SDK identity decode never sees the actual price.
        return flight

    monkeypatch.setattr(_decoders, "parse_flight_row", decode)
    return flight


def payload(amount=Decimal("6144602.123456789")):
    return {
        "data": [None, None, [[[[], [[None, amount], "synthetic-token"]]]], None],
        "url": "https://www.google.com/travel/flights?tfs=synthetic-request",
    }


def provider():
    return FliProvider(
        zone_resolver=lambda airport: {"HND": "Asia/Tokyo", "CGK": "Asia/Jakarta"}[airport]
    )


def test_exact_prices_identity_and_conservative_evidence(decoder):
    p = provider()
    try:
        source = payload()
        r = p.normalize(source, query())
        o = r.offers_by_itinerary_index[0][0]
        assert o.amount_original.amount == Decimal("6144602.123456789")
        assert source["data"][2][0][0][1][0][-1] == Decimal("6144602.123456789")
        assert o.provider_id == "fli" and o.hidden_city == "unknown"
        assert o.price_status == "indicative" and o.provider_quote_handle is None
        assert o.link_scope == "generic_search"
        assert r.itineraries[0][0].depart_at.utcoffset() == timedelta(hours=9)
        assert r.itineraries[0][0].arrive_at.utcoffset() == timedelta(hours=7)
    finally:
        p.blocking.close()


@pytest.mark.parametrize("amount", [True, 1.2, Decimal(-1), 0])
def test_reject_float_bool_negative_prices(decoder, amount):
    p = provider()
    try:
        with pytest.raises(ProviderFailure, match="invalid_price"):
            p.normalize(payload(amount), query())
    finally:
        p.blocking.close()


def test_wrong_currency_or_route_cannot_commit(decoder):
    p = provider()
    try:
        decoder.currency = "USD"
        with pytest.raises(ProviderFailure, match="invalid_currency"):
            p.normalize(payload(), query())
        decoder.currency = "IDR"
        decoder.legs[0].departure_airport.name = "NRT"
        with pytest.raises(ProviderFailure, match="schema_changed"):
            p.normalize(payload(), query())
    finally:
        p.blocking.close()


def test_valid_empty_vs_unpriced_and_missing_payload(decoder):
    p = provider()
    try:
        r = p.normalize({"data": [None, None, [[], None], None]}, query())
        assert r.status == "succeeded_empty" and r.unpriced_candidate_count == 0
        assert r.provider_complete is False
        r = p.normalize({"data": [None, None, [[[[], [[], "token"]]]], None]}, query())
        assert r.status == "succeeded_empty" and r.unpriced_candidate_count == 1
        with pytest.raises(ProviderFailure, match="schema_changed"):
            p.normalize({"data": None}, query())
        with pytest.raises(ProviderFailure, match="schema_changed"):
            p.normalize({"data": [None, None, None, None]}, query())
    finally:
        p.blocking.close()


async def test_unsupported_basic_filter_never_sends():
    p = provider()
    q = query()
    from dataclasses import replace

    try:
        with pytest.raises(ProviderFailure, match="unsupported_query"):
            await p.search(replace(q, include_basic_economy=False))
    finally:
        p.blocking.close()


def test_retry_after_stops_unsent_peer_and_blocks_no_identity_switch():
    p = provider()
    calls = []

    class Session:
        def get(self, *a, **kw):
            calls.append(kw)
            return SimpleNamespace(status_code=429, headers={"Retry-After": "70"})

    try:
        for _ in range(2):
            with pytest.raises(ProviderFailure) as caught:
                p._get(Session(), "https://www.google.com/travel/flights")
            assert caught.value.code == "http_rate_limited"
            assert 0 < caught.value.retry_after_seconds <= 70
        assert len(calls) == 1
    finally:
        p.blocking.close()


@pytest.mark.parametrize(
    "target",
    [
        "https://www.google.com/sorry/index",
        "https://consent.google.com/",
        "https://example.invalid/",
        "https://www.google.com/travel/flights/unsupported",
    ],
)
def test_challenge_redirect_is_not_followed(target):
    p = provider()
    calls = []

    class Session:
        def get(self, *a, **kw):
            calls.append(a)
            return SimpleNamespace(status_code=302, headers={"location": target})

    try:
        for _ in range(2):
            with pytest.raises(ProviderFailure, match="auth_denied"):
                p._get(Session(), "https://www.google.com/travel/flights")
        assert len(calls) == 1
    finally:
        p.blocking.close()


async def test_c3_real_threads_overlap_and_cancel_retains_physical_capacity(decoder):
    p = provider()
    entered = threading.Barrier(4)
    release = threading.Event()

    def fetch(q):
        entered.wait(timeout=5)
        release.wait(timeout=5)
        return payload()

    p._fetch = fetch
    tasks = [asyncio.create_task(p.search(query())) for _ in range(3)]
    try:
        await asyncio.to_thread(entered.wait, 5)
        assert p.blocking.busy == 3
        tasks[0].cancel()
        await asyncio.gather(tasks[0], return_exceptions=True)
        assert p.blocking.busy == 3
        with pytest.raises(ProviderFailure, match="provider_unavailable"):
            await p.search(query())
        release.set()
        await asyncio.gather(*tasks, return_exceptions=True)
        await p.blocking.drain()
        assert p.blocking.busy == 0
    finally:
        release.set()
        await p.blocking.drain()
        p.blocking.close()


def test_fetch_pins_http2_and_preserves_json_price_lexemes(monkeypatch):
    pytest.importorskip("fli")
    import curl_cffi.requests
    from curl_cffi import CurlHttpVersion

    state = {}

    class Session:
        def __init__(self, **kw):
            state.update(kw)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            state["closed"] = True

    monkeypatch.setattr(curl_cffi.requests, "Session", Session)
    p = provider()
    import json

    body = json.dumps(payload(1)["data"]).replace("[null, 1]", "[null, 6144602.123456789]")
    html = "AF_initDataCallback({key: 'ds:1', data:" + body + ", sideChannel: {}});"
    p._get = lambda session, url: (html, url)
    try:
        result = p._fetch(query())
        assert state["http_version"] == CurlHttpVersion.V2TLS and state["closed"]
        assert result["data"][2][0][0][1][0][-1] == Decimal("6144602.123456789")
    finally:
        p.blocking.close()
