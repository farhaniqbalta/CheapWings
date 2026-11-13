//! Exact money arithmetic, byte-compatible with `backend/src/cheapwings/domain/money.py`.
//! Amounts cross boundaries as decimal text; floats never appear.

use rust_decimal::prelude::ToPrimitive;
use rust_decimal::{Decimal, RoundingStrategy};
use std::fmt;
use std::str::FromStr;

/// ISO 4217 minor-unit exponents. Unknown currencies fail closed rather than assuming 2.
const EXPONENTS: &[(&str, u32)] = &[
    ("IDR", 0), ("JPY", 0), ("KRW", 0), ("VND", 0),
    ("USD", 2), ("AUD", 2), ("EUR", 2), ("GBP", 2), ("CAD", 2), ("SGD", 2), ("MYR", 2),
    ("INR", 2), ("CNY", 2), ("HKD", 2), ("NZD", 2), ("CHF", 2), ("THB", 2), ("PHP", 2),
    ("BRL", 2), ("MXN", 2), ("CZK", 2), ("DKK", 2), ("SEK", 2), ("PLN", 2), ("RON", 2),
    ("TRY", 2), ("TWD", 2), ("UAH", 2),
];

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MoneyError {
    UnknownCurrency(String),
    InvalidDecimal(String),
    NotWholeMinorUnits,
    Overflow,
}

impl fmt::Display for MoneyError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::UnknownCurrency(c) => write!(f, "unknown_currency: minor-unit exponent for {c:?} is not configured"),
            Self::InvalidDecimal(t) => write!(f, "invalid decimal amount {t:?}"),
            Self::NotWholeMinorUnits => write!(f, "amount does not scale cleanly to the currency's minor units"),
            Self::Overflow => write!(f, "amount out of range"),
        }
    }
}

impl std::error::Error for MoneyError {}

pub fn minor_unit_exponent(currency: &str) -> Result<u32, MoneyError> {
    let code = currency.to_uppercase();
    EXPONENTS
        .iter()
        .find(|(c, _)| *c == code)
        .map(|(_, e)| *e)
        .ok_or(MoneyError::UnknownCurrency(currency.to_owned()))
}

fn parse(text: &str) -> Result<Decimal, MoneyError> {
    let parsed = if text.contains(['e', 'E']) { Decimal::from_scientific(text) } else { Decimal::from_str(text) };
    parsed.map_err(|_| MoneyError::InvalidDecimal(text.to_owned()))
}

/// `Decimal(minor).scaleb(-exponent)` as text, scale preserved (`100` USD → `"1.00"`).
pub fn from_minor_units(minor: i128, currency: &str) -> Result<String, MoneyError> {
    Decimal::try_from_i128_with_scale(minor, minor_unit_exponent(currency)?)
        .map(|d| d.to_string())
        .map_err(|_| MoneyError::Overflow)
}

/// `Money.as_minor_units`: exact scale-up; fails if the result is not a whole number.
pub fn as_minor_units(amount: &str, currency: &str) -> Result<i128, MoneyError> {
    let exp = minor_unit_exponent(currency)?;
    let scaled = parse(amount)?
        .checked_mul(Decimal::from(10u64.pow(exp)))
        .ok_or(MoneyError::Overflow)?;
    if !scaled.fract().is_zero() {
        return Err(MoneyError::NotWholeMinorUnits);
    }
    scaled.trunc().to_i128().ok_or(MoneyError::Overflow)
}

/// `FXSnapshot.convert`: amount × rate, half-even to the quote currency's minor units,
/// scale padded like `Decimal.quantize`.
pub fn fx_convert(amount: &str, rate: &str, quote_currency: &str) -> Result<String, MoneyError> {
    let exp = minor_unit_exponent(quote_currency)?;
    let product = parse(amount)?.checked_mul(parse(rate)?).ok_or(MoneyError::Overflow)?;
    let mut rounded = product.round_dp_with_strategy(exp, RoundingStrategy::MidpointNearestEven);
    rounded.rescale(exp);
    let text = rounded.to_string();
    // Python keeps the sign of a negative product that rounds to zero ("-0.00").
    Ok(if product.is_sign_negative() && rounded.is_zero() { format!("-{text}") } else { text })
}
