"""Money through the public Python API is backed by the shared Rust core (P5.1)."""

import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

from cheapwings.domain import money
from cheapwings.domain.money import FXSnapshot, Money, UnknownCurrencyError

FIXTURES = Path(__file__).resolve().parents[3] / "contracts" / "fixtures" / "core" / "core_fixtures.json"


def _python_api_result(case):
    try:
        if case["op"] == "fx":
            snapshot = FXSnapshot("USD", case["currency"], Decimal(case["rate"]), "fixture", "t")
            return str(snapshot.convert(Money(Decimal(case["amount"]), "USD")).amount)
        if case["op"] == "from_minor":
            return str(Money.from_minor_units(int(case["minor"]), case["currency"]).amount)
        return str(Money(Decimal(case["amount"]), case["currency"]).as_minor_units())
    except ValueError:
        return None


def test_money_fixtures_through_python_api():
    cases = json.loads(FIXTURES.read_text())["money"]
    wrong = [c for c in cases if _python_api_result(c) != c["expect"]]
    assert not wrong, f"{len(wrong)} mismatches, first: {wrong[0]}"
    assert len(cases) == 3006


def test_unknown_currency_raises_unknown_currency_error():
    with pytest.raises(UnknownCurrencyError):
        money.minor_unit_exponent("XYZ")
    with pytest.raises(UnknownCurrencyError):
        Money.from_minor_units(1, "XYZ")


def test_beyond_28_digits_is_exact():
    # Behaviour change in P5.1: Python's 28-digit context used to round this; Rust is exact.
    amount = Money(Decimal("79228162514264337593543950335"), "IDR")
    assert amount.as_minor_units() == 79228162514264337593543950335


def test_beyond_96_bit_raises_instead_of_rounding():
    # Rust decimals hold at most a 96-bit mantissa (~7.9e28). Old Python rounded silently.
    with pytest.raises(ValueError):
        Money(Decimal("123456789012345678901234567890"), "JPY").as_minor_units()
    with pytest.raises(ValueError):
        Money(Decimal("79228162514264337593543950335"), "USD").as_minor_units()
    with pytest.raises(ValueError):
        Money.from_minor_units(10**30, "USD")


def test_core_module_is_rust():
    import cheapwings_core

    assert money.minor_unit_exponent.__module__ == "cheapwings.domain.money"
    # maturin ships a package whose __init__ re-exports the compiled extension's functions.
    assert type(cheapwings_core.fx_convert).__name__ == "builtin_function_or_method"
    assert money._core is cheapwings_core


def test_missing_core_module_names_the_fix():
    code = "import sys; sys.modules['cheapwings_core'] = None; import cheapwings.domain.money"
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode != 0
    assert "maturin develop" in result.stderr
