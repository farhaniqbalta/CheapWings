"""P7.8: one foreign-currency offer no longer fails a whole Fli route (live P7.7: HRB, CDG, PER, LHR)."""

from datetime import date

import pytest
from backend.tests.unit.test_p57_parsers import fli_payload, require_fli

from cheapwings.domain.evidence import ProviderFailure
from cheapwings.providers.base import SingleDateRouteQuery
from cheapwings.providers.fli import FliProvider

Q = SingleDateRouteQuery("HND", "CGK", date(2027, 1, 2), True, False, "IDR")


def test_mixed_currency_keeps_display_currency_offers():
    require_fli()
    payload = fli_payload()
    payload["data"][3] = fli_payload(currency="USD")["data"][2]
    provider = FliProvider()
    try:
        result = provider.normalize(payload, Q)
    finally:
        provider.blocking.close()
    assert result.status == "succeeded_results"
    assert [o[0].amount_original.currency for o in result.offers_by_itinerary_index] == ["IDR"]
    assert result.unpriced_candidate_count == 1  # the USD offer is counted, not shown
    assert result.provider_complete is False


def test_no_offer_in_display_currency_still_fails():
    require_fli()
    provider = FliProvider()
    try:
        with pytest.raises(ProviderFailure, match="invalid_currency"):
            provider.normalize(fli_payload(currency="USD"), Q)
    finally:
        provider.blocking.close()
