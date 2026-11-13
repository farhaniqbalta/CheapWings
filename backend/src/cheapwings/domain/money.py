"""Exact monetary values. Float is forbidden for money anywhere in this codebase.

Arithmetic (minor units, FX rounding) and the ISO 4217 minor-unit table live in the shared
Rust core (`core/cheapwings-core`), so the web backend and the iPad app compute identically.
Values cross into Rust as decimal text; this module keeps the Python types and validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

try:
    import cheapwings_core as _core
except ImportError as exc:
    raise ImportError(
        "cheapwings_core is not built; run: "
        ".venv/bin/maturin develop --release -m core/cheapwings-py/Cargo.toml"
    ) from exc


class UnknownCurrencyError(ValueError):
    """Raised when a currency's minor-unit convention is not configured."""


def _core_call(function, *args):
    """Call the Rust core, mapping its errors onto this module's exception types."""
    try:
        return function(*args)
    except ValueError as exc:
        if str(exc).startswith("unknown_currency:"):
            raise UnknownCurrencyError(
                f"{exc}; add it explicitly rather than assuming 2."
            ) from exc
        raise
    except OverflowError as exc:  # integers beyond the core's 128-bit range
        raise ValueError(f"amount out of range: {exc}") from exc


def minor_unit_exponent(currency: str) -> int:
    return _core_call(_core.minor_unit_exponent, currency)


@dataclass(frozen=True, slots=True)
class Money:
    """An exact amount in a single ISO 4217 currency.

    Amount is always a Decimal. There is no float constructor path: callers
    parsing JSON must use a Decimal-aware parser (e.g. `json.loads(text,
    parse_float=Decimal)`) before this type is ever touched.
    """

    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise TypeError(
                f"Money.amount must be a Decimal, got {type(self.amount).__name__}. "
                "float is forbidden for monetary values."
            )
        object.__setattr__(self, "currency", self.currency.upper())
        if len(self.currency) != 3 or not self.currency.isalpha():
            raise ValueError(f"currency must be a 3-letter ISO 4217 code, got {self.currency!r}")

    @classmethod
    def from_str(cls, amount: str, currency: str) -> Money:
        try:
            return cls(Decimal(amount), currency)
        except InvalidOperation as exc:
            raise ValueError(f"Invalid decimal amount string: {amount!r}") from exc

    @classmethod
    def from_minor_units(cls, minor_units: int, currency: str) -> Money:
        return cls(Decimal(_core_call(_core.from_minor_units, minor_units, currency)), currency)

    def require_same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot compare/combine {self.currency} with {other.currency} "
                "without an explicit FX conversion step."
            )

    def __add__(self, other: Money) -> Money:
        self.require_same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __lt__(self, other: Money) -> bool:
        self.require_same_currency(other)
        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        self.require_same_currency(other)
        return self.amount <= other.amount

    def as_minor_units(self) -> int:
        return _core_call(_core.as_minor_units, str(self.amount), self.currency)

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"


@dataclass(frozen=True, slots=True)
class FXSnapshot:
    """A single conversion rate observation, never silently reused across unrelated prices."""

    base_currency: str
    quote_currency: str
    rate: Decimal
    source: str
    retrieved_at: str  # ISO 8601 UTC instant; kept as str at the domain boundary

    def convert(self, amount: Money) -> Money:
        if amount.currency != self.base_currency:
            raise ValueError(
                f"FXSnapshot base is {self.base_currency}, cannot convert {amount.currency}"
            )
        converted = _core_call(
            _core.fx_convert, str(amount.amount), str(self.rate), self.quote_currency
        )
        return Money(Decimal(converted), self.quote_currency)
