from datetime import date

import pytest

from cheapwings.domain.coverage import WorkStatus
from cheapwings.domain.offer import ProviderErrorCode
from cheapwings.providers.base import SingleDateRouteQuery
from cheapwings.providers.fake import SYNTHETIC_LABEL, FakeProvider, ScriptedOutcome


def _query(**overrides):
    defaults = dict(
        origin="MEL",
        destination="DPS",
        departure_date=date(2026, 12, 16),
        include_basic_economy=True,
        include_hidden_city=False,
        display_currency="IDR",
    )
    defaults.update(overrides)
    return SingleDateRouteQuery(**defaults)


@pytest.mark.asyncio
async def test_fake_provider_returns_deterministic_results():
    provider = FakeProvider()
    result1 = await provider.search(_query())
    result2 = await provider.search(_query())
    assert result1.status == WorkStatus.SUCCEEDED_RESULTS
    assert result1.offers_by_itinerary_index[0][0].amount_original.amount == (
        result2.offers_by_itinerary_index[0][0].amount_original.amount
    )


@pytest.mark.asyncio
async def test_fake_provider_labels_prices_as_synthetic():
    provider = FakeProvider()
    result = await provider.search(_query())
    assert all(
        SYNTHETIC_LABEL in offer.seller
        for offers in result.offers_by_itinerary_index
        for offer in offers
    )


@pytest.mark.asyncio
async def test_fake_provider_respects_idr_zero_minor_units():
    provider = FakeProvider()
    result = await provider.search(_query(display_currency="IDR"))
    for offer in result.offers_by_itinerary_index[0]:
        assert offer.amount_original.amount == offer.amount_original.amount.to_integral_value()


@pytest.mark.asyncio
async def test_fake_provider_respects_include_basic_economy_false():
    provider = FakeProvider()
    result = await provider.search(_query(include_basic_economy=False))
    offers = result.offers_by_itinerary_index[0]
    assert all(not o.basic_economy for o in offers)


@pytest.mark.asyncio
async def test_fake_provider_scripted_failure_is_not_empty_success():
    provider = FakeProvider()
    provider.script(
        "MEL", "XXX", date(2026, 12, 16),
        ScriptedOutcome(status=WorkStatus.FAILED_TERMINAL, error_code=ProviderErrorCode.NETWORK_TIMEOUT),
    )
    result = await provider.search(_query(destination="XXX"))
    assert result.status == WorkStatus.FAILED_TERMINAL
    assert result.error_code == ProviderErrorCode.NETWORK_TIMEOUT
    assert result.itineraries == ()


@pytest.mark.asyncio
async def test_fake_provider_scripted_empty_is_distinct_from_failure():
    provider = FakeProvider()
    provider.script("MEL", "YYY", date(2026, 12, 16), ScriptedOutcome(status=WorkStatus.SUCCEEDED_EMPTY))
    result = await provider.search(_query(destination="YYY"))
    assert result.status == WorkStatus.SUCCEEDED_EMPTY
    assert result.error_code is None
