from datetime import date

import pytest
from pydantic import ValidationError

from cheapwings.domain.query import SearchQuery


def _base(**overrides):
    defaults = dict(
        origins=["MEL"],
        destinations=["DPS"],
        departure_date_from=date(2026, 12, 12),
        departure_date_through=date(2026, 12, 20),
        display_currency="IDR",
    )
    defaults.update(overrides)
    return defaults


def test_rejects_same_origin_and_destination():
    with pytest.raises(ValidationError):
        SearchQuery(**_base(origins=["MEL"], destinations=["MEL"]))


def test_rejects_reversed_dates():
    with pytest.raises(ValidationError):
        SearchQuery(**_base(departure_date_from=date(2026, 12, 20), departure_date_through=date(2026, 12, 12)))


def test_rejects_invalid_iata():
    with pytest.raises(ValidationError):
        SearchQuery(**_base(origins=["ME1"]))


def test_rejects_roundtrip_in_mvp():
    with pytest.raises(ValidationError):
        SearchQuery(**_base(trip_type="round_trip"))


def test_rejects_multi_adult_in_mvp():
    with pytest.raises(ValidationError):
        SearchQuery(**_base(adults=2))


def test_include_hidden_city_defaults_false_and_does_not_silently_flip():
    q = SearchQuery(**_base())
    assert q.include_hidden_city is False


def test_rejects_excessive_combination_count():
    with pytest.raises(ValidationError):
        SearchQuery(
            **_base(
                origins=["MEL", "SYD", "BNE", "PER", "ADL"],
                destinations=["CGK", "DPS", "SUB", "JOG", "SRG"],
                departure_date_from=date(2026, 12, 1),
                departure_date_through=date(2026, 12, 31),
                max_combinations=120,
            )
        )
