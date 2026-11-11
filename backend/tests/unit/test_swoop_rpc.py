import json
from datetime import date
from types import SimpleNamespace

import pytest

from cheapwings.domain.evidence import ProviderFailure
from cheapwings.providers.base import SingleDateRouteQuery
from cheapwings.providers.swoop import SwoopProvider
from cheapwings.providers.swoop_search import parse_search_response

pytest.importorskip("swoop")


@pytest.mark.parametrize(
    "code,error,delay",
    [
        (13, "provider_unavailable", 0),
        (8, "http_rate_limited", 120),
        (7, "auth_denied", 0),
        (16, "auth_denied", 0),
        (4, "network_timeout", 0),
    ],
)
def test_short_rpc_error_is_not_empty_success(code, error, delay):
    text = json.dumps([["wrb.fr", None, None, None, None, [code]]])
    with pytest.raises(ProviderFailure) as caught:
        parse_search_response(text)
    assert caught.value.code == error
    assert caught.value.retry_after_seconds == delay


@pytest.mark.parametrize(
    "text",
    [
        "",
        "[]",
        "null",
        "{}",
        '[["wrb.fr",null,null]]',
        '[["wrb.fr",null,"null"]]',
        '[["wrb.fr",null,"[]"]]',
    ],
)
def test_missing_or_malformed_payload_is_not_empty_success(text):
    with pytest.raises(ProviderFailure, match="schema_changed"):
        parse_search_response(text)


def test_valid_empty_with_metadata_frame_is_preserved():
    text = ")]}'\n" + json.dumps(
        [["di", 100], ["wrb.fr", None, json.dumps([None, None, [[], None], [[], None]])]]
    )
    result = parse_search_response(text)
    assert result.best == [] and result.other == []


def test_adapter_rejects_short_error_before_normalization(monkeypatch):
    from swoop import rpc

    monkeypatch.setattr(
        rpc,
        "_http_post",
        lambda *a, **kw: SimpleNamespace(text='[["wrb.fr",null,null,null,null,[13]]]'),
    )
    provider = SwoopProvider()
    query = SingleDateRouteQuery("HND", "CGK", date(2026, 11, 20), True, False, "IDR")
    try:
        with pytest.raises(ProviderFailure, match="provider_unavailable"):
            provider._invoke("search", query, "ID")
    finally:
        provider.blocking.close()


def test_guard_keeps_sdk_priced_offer_construction(monkeypatch):
    import swoop._selection as selection
    from swoop import rpc

    from cheapwings.providers.swoop_search import search

    itinerary = object()
    option = object()
    raw = SimpleNamespace(best=[itinerary], other=[], price_range=None)
    monkeypatch.setattr(
        rpc,
        "_http_post",
        lambda *a, **kw: SimpleNamespace(
            text=json.dumps([["wrb.fr", None, json.dumps([None, None, [], []])]])
        ),
    )
    monkeypatch.setattr(rpc, "_parse_rpc_response", lambda text: raw)

    def build(legs, itineraries, **kw):
        assert legs[0]["origin"] == "HND"
        assert itineraries == [itinerary]
        assert kw["include_basic_economy"] is True
        return option

    monkeypatch.setattr(selection, "_build_trip_option", build)
    query = SingleDateRouteQuery("HND", "CGK", date(2026, 11, 20), True, False, "IDR")
    result = search(query, SimpleNamespace())
    assert result.results == [option]
    assert result.is_complete is True
