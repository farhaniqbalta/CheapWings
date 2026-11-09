from decimal import Decimal

import pytest

from cheapwings.domain.money import FXSnapshot, Money, UnknownCurrencyError


def test_money_rejects_float():
    with pytest.raises(TypeError):
        Money(1.5, "USD")  # type: ignore[arg-type]


def test_money_requires_known_currency_for_minor_units():
    with pytest.raises(UnknownCurrencyError):
        Money.from_minor_units(1000, "XYZ")


def test_idr_has_zero_minor_units():
    m = Money.from_minor_units(2_850_000, "IDR")
    assert m.amount == Decimal(2850000)


def test_usd_has_two_minor_units():
    m = Money.from_minor_units(27100, "USD")
    assert m.amount == Decimal("271.00")


def test_cannot_compare_different_currencies():
    usd = Money(Decimal(100), "USD")
    idr = Money(Decimal(100), "IDR")
    with pytest.raises(ValueError):
        _ = usd < idr


def test_fx_snapshot_converts():
    snap = FXSnapshot(
        base_currency="USD",
        quote_currency="IDR",
        rate=Decimal("18108.7"),
        source="skiplagged",
        retrieved_at="2026-11-09T11:47:15Z",
    )
    converted = snap.convert(Money(Decimal(271), "USD"))
    assert converted.currency == "IDR"
    assert converted.amount == Decimal(4907458)  # 271 * 18108.7, rounded to 0 minor units
