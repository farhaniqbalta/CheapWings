"""Recorded P0 snapshots are evidence, not current quotes. No external calls."""
import asyncio
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from cheapwings.domain.evidence import ProviderFailure
from cheapwings.providers.base import RepriceRequest, SingleDateRouteQuery
from cheapwings.providers.common import json_payload
from cheapwings.providers.exact_json import ExactCapture
from cheapwings.providers.skiplagged import SkiplaggedProvider
from cheapwings.providers.swoop import BoundedCall, SwoopProvider, local_instant

FIXTURES = Path(__file__).parents[3] / 'contracts/fixtures/provider'


def query(**patch):
    from dataclasses import replace
    return replace(SingleDateRouteQuery('MEL','DPS',date(2026,12,16),True,False,'IDR'), **patch)


def load(name):
    return json_payload((FIXTURES / name).read_text())


def zones(code):
    # Injected reference fixture only; production uses versioned airportsdata.
    return {'MEL':'Australia/Melbourne','SYD':'Australia/Sydney','NTL':'Australia/Sydney',
            'DPS':'Asia/Makassar','CGK':'Asia/Jakarta','SIN':'Asia/Singapore',
            'KUL':'Asia/Kuala_Lumpur','BNE':'Australia/Brisbane','ADL':'Australia/Adelaide',
            'PER':'Australia/Perth'}[code]


def test_skiplagged_exact_money_unknown_fields_and_no_fake_segments():
    p = SkiplaggedProvider()
    payload = load('skiplagged_probe_20261109T123430Z.json')['search_structured_content']
    result = p.normalize(payload, query())
    assert len(result.itineraries) == 5
    assert all(s == () for s in result.itineraries)
    assert result.provider_complete is False
    o = result.offers_by_itinerary_index[0][0]
    assert o.amount_original.amount == Decimal(271)
    assert o.amount_original.currency == 'USD'
    assert o.comparable_amount.amount == Decimal(4907458)
    assert o.evidence.fx_snapshot.rate == Decimal('18108.7')
    assert o.hidden_city == 'no' and o.price_status == 'indicative'
    assert o.seller is None and o.basic_economy is None
    assert result.itinerary_summaries[0].duration_minutes == 360


async def test_skiplagged_request_filters_and_fail_closed():
    captured = []
    async def transport(args):
        captured.append(args)
        return {'flights': [], 'pagination': {'hasMoreResults': False}}
    provider = SkiplaggedProvider(transport)
    result = await provider.search(query(include_hidden_city=True))
    assert result.status == 'succeeded_empty'
    assert captured[0]['includeHiddenCity'] is False
    assert captured[0]['includeVirtualInterlining'] is False
    with pytest.raises(ProviderFailure, match='unsupported_query'):
        await provider.search(query(include_basic_economy=False))
    from cheapwings.providers.common import decimal_value
    with pytest.raises(ProviderFailure):
        decimal_value(1.1)


def test_mcp_capture_preserves_sse_decimals():
    capture = ExactCapture()
    event = b'data: {"result":{"structuredContent":{"flights":[],"pricing":{"rate":18108.7}}}}\n\n'
    for start in range(0, len(event), 7):
        capture.feed(event[start:start+7])
    assert capture.result['pricing']['rate'] == Decimal('18108.7')


def test_swoop_p0_timezone_identity_and_unknown_risk():
    p = SwoopProvider(zone_resolver=zones)
    payload = load('swoop_probe_20261109T123521Z.json')['search_result']
    result = p.normalize_search(payload, query())
    assert len(result.itineraries) + result.unpriced_candidate_count == 11
    assert result.itineraries[0][0].depart_at.isoformat() == '2026-12-16T06:30:00+11:00'
    assert result.offers_by_itinerary_index[0][0].hidden_city == 'unknown'
    assert result.offers_by_itinerary_index[0][0].seller is None
    assert result.provider_complete is True
    p.blocking.close()


async def test_swoop_seller_basic_mismatch_and_estimate_never_exact():
    fixture = load('swoop_probe_20261109T123521Z.json')
    async def price(selector):
        return fixture['price_result']
    p = SwoopProvider(price_transport=price, zone_resolver=zones)
    result = p.normalize_search(fixture['search_result'], query())
    offer = result.offers_by_itinerary_index[0][0]
    priced = await p.reprice(RepriceRequest(offer, result.itineraries[0], query()))
    assert len(priced.offers) == 1
    o = priced.offers[0]
    assert o.seller == 'Jetabroad' and o.basic_economy is True
    assert o.is_estimate is True and o.price_status == 'indicative'
    assert o.amount_original.amount == Decimal(7767558)
    assert priced.exact_product_match is False
    assert o.link is None  # signed URL intentionally not persisted/exposed
    fixture['price_result']['is_estimate'] = False
    priced = await p.reprice(RepriceRequest(offer, result.itineraries[0], query()))
    assert priced.offers[0].price_status == 'recent_search'
    assert priced.offers[0].repriced_at is None
    p.blocking.close()


def test_missing_zone_retains_unmatched_summary():
    p = SwoopProvider(zone_resolver=lambda _: (_ for _ in ()).throw(KeyError()))
    fixture = load('swoop_probe_20261109T123521Z.json')
    result = p.normalize_search(fixture['search_result'], query())
    assert result.itineraries[0] == ()
    assert result.itinerary_summaries[0].depart_at.tzinfo is None
    assert 'unresolved' in result.itinerary_summaries[0].warnings[0]
    p.blocking.close()


def test_dst_ambiguity_rejected():
    with pytest.raises(ProviderFailure, match='missing_segments'):
        local_instant([2026,11,1],[1,30],'X',lambda _: 'America/New_York')
    with pytest.raises(ProviderFailure):
        local_instant([2026,3,8],[2,30],'X',lambda _: 'America/New_York')


async def test_real_thread_slot_retained_on_cancellation():
    import threading
    started, release = threading.Event(), threading.Event()
    def blocking():
        started.set()
        release.wait(2)
    runner = BoundedCall()
    task = asyncio.create_task(runner.run(blocking))
    while not started.is_set():
        await asyncio.sleep(.001)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    with pytest.raises(ProviderFailure):
        await runner.run(lambda: None)
    release.set()
    while not runner.future.done():
        await asyncio.sleep(.001)
    assert await runner.run(lambda: 7) == 7
    runner.close()
