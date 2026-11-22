"""P7.4 web discovery adapter: Skiplagged anywhere through the shared Rust parser (no network)."""

import json
from datetime import date
from pathlib import Path

import pytest

from cheapwings.domain.evidence import ProviderFailure
from cheapwings.providers.base import DiscoveryRequest, ProviderCapabilities
from cheapwings.providers.common import json_payload
from cheapwings.providers.exact_json import ExactCapture
from cheapwings.providers.fake import FakeProvider
from cheapwings.providers.skiplagged import SkiplaggedProvider

FIXTURE = Path(__file__).resolve().parents[3] / "contracts" / "fixtures" / "core" / "discovery_sources_fixtures.json"
CASES = {c["name"]: c for c in json.loads(FIXTURE.read_text())["anywhere"]}


def recorded_payload(name="probe_SUB_2026-12-22"):
    """The structured content of a recorded P7.1 reply, with exact Decimal numbers like mcp_search returns."""
    return json_payload(json.dumps(json.loads(CASES[name]["rpc_json"])["result"]["structuredContent"]))


REQUEST = DiscoveryRequest("SUB", date(2026, 12, 22), "IDR")


async def test_recorded_reply_becomes_observations():
    sent = []

    async def transport(args):
        sent.append(args)
        return recorded_payload()

    result = await SkiplaggedProvider(discovery_transport=transport).discover(REQUEST)
    assert sent == [{"from": "SUB", "depart": "2026-12-22", "currency": "IDR", "fare_class": "economy", "adults": 1}]
    assert result.provider_id == "skiplagged" and result.request == REQUEST
    assert len(result.observations) == 42 and result.unpriced == 0
    first = result.observations[0]
    assert (first["destination"], first["amount"], first["currency"], first["hidden_city"]) == ("DPS", "46", "USD", "no")
    assert result.fx == ({"currency": "USD", "rate": "18292.9"},)


async def test_malformed_reply_is_schema_changed():
    async def transport(args):
        return {"pricing": {}}

    with pytest.raises(ProviderFailure, match="schema_changed"):
        await SkiplaggedProvider(discovery_transport=transport).discover(REQUEST)


async def test_transport_failures_pass_through():
    async def limited(args):
        raise ProviderFailure("rate_limited", 30)

    with pytest.raises(ProviderFailure) as caught:
        await SkiplaggedProvider(discovery_transport=limited).discover(REQUEST)
    assert (caught.value.code, caught.value.retry_after_seconds) == ("rate_limited", 30)


def test_capability_flag_is_last_with_default():
    assert ProviderCapabilities(True, False, False, True, True, False).destination_discovery is False
    assert SkiplaggedProvider.capabilities.destination_discovery is True
    assert SkiplaggedProvider.capabilities.detailed_search is True


def test_anywhere_capture_keeps_exact_numbers():
    capture = ExactCapture("results")
    capture.feed(b'data: {"result":{"structuredContent":{"results":[],"pricing":{"rate":18292.9}}}}\n\n')
    assert str(capture.result["pricing"]["rate"]) == "18292.9"
    assert ExactCapture().key == "flights"


async def test_fake_discovery_is_scripted_and_synthetic():
    fake = FakeProvider(discovery_destinations=("DPS", "SIN"))
    result = await fake.discover(DiscoveryRequest("CGK", date(2027, 3, 1), "IDR"))
    assert [o["destination"] for o in result.observations] == ["DPS", "SIN"]
    assert all(o["departure_date"] == "2027-03-01" and o["origin"] == "CGK" for o in result.observations)
    fake.script_discovery("CGK", "2027-03-02", ProviderFailure("rate_limited", 5))
    with pytest.raises(ProviderFailure, match="rate_limited"):
        await fake.discover(DiscoveryRequest("CGK", date(2027, 3, 2), "IDR"))
