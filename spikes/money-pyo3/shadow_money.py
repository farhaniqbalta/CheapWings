"""S4 pytest plugin: shadow every money operation through Rust during the real backend suite.

Python's result is always returned, so suite behaviour is unchanged; any Rust disagreement
(value, exact text, or one side failing) is collected and fails the session at the end.

Run from backend/: PYTHONPATH=src:../spikes/money-pyo3 python -m pytest -p shadow_money
"""

from decimal import Decimal

import cheapwings_money_rs as rs
from cheapwings.domain import money as m

calls = {"exp": 0, "from_minor": 0, "as_minor": 0, "fx": 0}
mismatches: list[str] = []


def _shadow(kind, label, python, rust):
    calls[kind] += 1
    try:
        expected = python()
    except Exception as python_error:
        try:
            rust()
        except Exception:  # noqa: BLE001 - both failed: agreement
            pass
        else:
            mismatches.append(f"{label}: python raised, rust returned")
        raise python_error  # always Python's own exception type
    try:
        got = rust()
    except Exception as exc:  # noqa: BLE001 - recorded, never changes the suite's result
        mismatches.append(f"{label}: rust raised {exc!r}, python={expected!r}")
        return expected
    if str(expected if not isinstance(expected, m.Money) else expected.amount) != str(got):
        mismatches.append(f"{label}: python={expected!r} rust={got!r}")
    return expected


def pytest_configure(config):
    original_exp = m.minor_unit_exponent
    original_from = m.Money.from_minor_units.__func__
    original_as = m.Money.as_minor_units
    original_convert = m.FXSnapshot.convert

    def minor_unit_exponent(currency):
        return _shadow("exp", f"exp {currency}", lambda: original_exp(currency),
                       lambda: rs.minor_unit_exponent(currency))

    def from_minor_units(cls, minor_units, currency):
        return _shadow("from_minor", f"from_minor {minor_units} {currency}",
                       lambda: original_from(cls, minor_units, currency),
                       lambda: rs.from_minor_units(minor_units, currency))

    def as_minor_units(self):
        return _shadow("as_minor", f"as_minor {self}", lambda: original_as(self),
                       lambda: rs.as_minor_units(str(self.amount), self.currency))

    def convert(self, amount):
        return _shadow("fx", f"fx {amount} x {self.rate}", lambda: original_convert(self, amount),
                       lambda: rs.fx_convert(str(amount.amount), str(Decimal(self.rate)), self.quote_currency))

    m.minor_unit_exponent = minor_unit_exponent
    m.Money.from_minor_units = classmethod(from_minor_units)
    m.Money.as_minor_units = as_minor_units
    m.FXSnapshot.convert = convert


def pytest_terminal_summary(terminalreporter):
    terminalreporter.write_line(f"S4 shadow money calls: {calls}; mismatches: {len(mismatches)}")
    for line in mismatches[:20]:
        terminalreporter.write_line(f"  MISMATCH {line}")


def pytest_sessionfinish(session):
    if mismatches:
        session.exitstatus = 1
