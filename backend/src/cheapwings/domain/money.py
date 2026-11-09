"""Exact monetary values. Float is forbidden for money anywhere in this codebase."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

# ISO 4217 minor-unit exponents for currencies this project is likely to see.
# Not exhaustive; unknown currencies fail closed rather than guessing 2.
_MINOR_UNIT_EXPONENTS: dict[str, int] = {
    "IDR": 0,
    "JPY": 0,
    "KRW": 0,
    "VND": 0,
    "USD": 2,
    "AUD": 2,
    "EUR": 2,
    "GBP": 2,
    "CAD": 2,
    "SGD": 2,
    "MYR": 2,
    "INR": 2,
    "CNY": 2,
    "HKD": 2,
    "NZD": 2,
    "CHF": 2,
    "THB": 2,
    "PHP": 2,
    "BRL": 2,
    "MXN": 2,
    "CZK": 2,
    "DKK": 2,
    "SEK": 2,
    "PLN": 2,
    "RON": 2,
    "TRY": 2,
    "TWD": 2,
    "UAH": 2,
}


class UnknownCurrencyError(ValueError):
    """Raised when a currency's minor-unit convention is not configured."""


def minor_unit_exponent(currency: str) -> int:
    try:
        return _MINOR_UNIT_EXPONENTS[currency.upper()]
    except KeyError as exc:
        raise UnknownCurrencyError(
            f"Minor-unit exponent for currency {currency!r} is not configured; "
            "add it explicitly rather than assuming 2."
        ) from exc


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
        exponent = minor_unit_exponent(currency)
        amount = Decimal(minor_units).scaleb(-exponent)
        return cls(amount, currency)

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
        exponent = minor_unit_exponent(self.currency)
        scaled = self.amount.scaleb(exponent)
        if scaled != scaled.to_integral_value():
            raise ValueError(
                f"Amount {self.amount} for {self.currency} does not scale cleanly "
                f"to {exponent} minor-unit digits."
            )
        return int(scaled)

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
        converted = (amount.amount * self.rate).quantize(
            Decimal(1).scaleb(-minor_unit_exponent(self.quote_currency))
        )
        return Money(converted, self.quote_currency)
