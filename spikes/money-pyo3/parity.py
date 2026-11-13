"""S4 parity grid: Rust money vs Python money on edge cases + 50k seeded random cases.

Run: PYTHONPATH=backend/src .venv/bin/python spikes/money-pyo3/parity.py
Compares values AND exact text (scale), and that both sides fail on the same inputs.
"""

import random
import sys
from decimal import Decimal

import cheapwings_money_rs as rs
from cheapwings.domain.money import FXSnapshot, Money, minor_unit_exponent

CURRENCIES = ["IDR", "JPY", "USD", "AUD", "EUR", "SGD", "usd", "XYZ"]
mismatches: list[str] = []
checked = 0


def same(label, py, rust):
    """Run both; both must fail, or both succeed with identical text."""
    global checked
    checked += 1
    try:
        expected = py()
    except (ValueError, ArithmeticError):
        expected = "<error>"
    try:
        got = rust()
    except (ValueError, OverflowError):
        got = "<error>"
    if str(expected) != str(got):
        mismatches.append(f"{label}: python={expected!r} rust={got!r}")


def py_convert(amount, rate, quote):
    return FXSnapshot("USD", quote, Decimal(rate), "parity", "t").convert(Money(Decimal(amount), "USD")).amount


def check(amount: str, rate: str, minor: int, currency: str):
    same(f"exp {currency}", lambda: minor_unit_exponent(currency), lambda: rs.minor_unit_exponent(currency))
    same(f"from_minor {minor} {currency}", lambda: Money.from_minor_units(minor, currency).amount,
         lambda: rs.from_minor_units(minor, currency))
    same(f"as_minor {amount} {currency}", lambda: Money(Decimal(amount), currency).as_minor_units(),
         lambda: rs.as_minor_units(amount, currency))
    same(f"fx {amount}*{rate}->{currency}", lambda: py_convert(amount, rate, currency),
         lambda: rs.fx_convert(amount, rate, currency))


EDGES = [
    ("0.125", "1", 0, "USD"), ("0.135", "1", 0, "USD"), ("2.5", "1", 0, "IDR"), ("3.5", "1", 0, "IDR"),
    ("-2.5", "1", -5, "IDR"), ("-0.004", "1", 0, "USD"), ("1.50", "1", 150, "USD"), ("1.505", "1", 1, "USD"),
    ("1E+3", "1.1", 10**18, "JPY"), ("0.1", "16234.123456789", 0, "IDR"), ("1250000", "0.0000613", 0, "USD"),
    ("0.0000000001", "0.0000000001", 0, "USD"),
]
for edge in EDGES:
    check(*edge)

# Known divergence, reported but not failing: beyond Python's default 28-digit context Python
# rounds as_minor_units silently and raises in convert; Rust stays exact. Unrealistic for fares.
before = len(mismatches)
check("79228162514264337593543950335", "1", 0, "IDR")
beyond_precision = mismatches[before:]
del mismatches[before:]

rng = random.Random(20261113)
for _ in range(50_000):
    places = rng.randint(0, 6)
    amount = str(Decimal(rng.randint(-10**12, 10**12)).scaleb(-places))
    rate = str(Decimal(rng.randint(1, 10**9)).scaleb(-rng.randint(0, 10)))
    check(amount, rate, rng.randint(-10**15, 10**15), rng.choice(CURRENCIES))

print(f"S4 parity: {checked} comparisons, {len(mismatches)} mismatches")
for line in beyond_precision:
    print("  KNOWN (>28 digits)", line)
for line in mismatches[:20]:
    print("  MISMATCH", line)
sys.exit(1 if mismatches else 0)
