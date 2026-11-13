//! Rust port of the arithmetic in `cheapwings/domain/money.py`. Values cross the boundary as
//! decimal text (never floats), so Python keeps its `Decimal`/`Money` types unchanged.

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use rust_decimal::prelude::ToPrimitive;
use rust_decimal::{Decimal, RoundingStrategy};
use std::str::FromStr;

/// Same table as `_MINOR_UNIT_EXPONENTS`; unknown currencies fail closed.
const EXPONENTS: &[(&str, u32)] = &[
    ("IDR", 0), ("JPY", 0), ("KRW", 0), ("VND", 0),
    ("USD", 2), ("AUD", 2), ("EUR", 2), ("GBP", 2), ("CAD", 2), ("SGD", 2), ("MYR", 2),
    ("INR", 2), ("CNY", 2), ("HKD", 2), ("NZD", 2), ("CHF", 2), ("THB", 2), ("PHP", 2),
    ("BRL", 2), ("MXN", 2), ("CZK", 2), ("DKK", 2), ("SEK", 2), ("PLN", 2), ("RON", 2),
    ("TRY", 2), ("TWD", 2), ("UAH", 2),
];

fn exponent(currency: &str) -> PyResult<u32> {
    let code = currency.to_uppercase();
    EXPONENTS
        .iter()
        .find(|(c, _)| *c == code)
        .map(|(_, e)| *e)
        .ok_or_else(|| PyValueError::new_err(format!("unknown_currency {currency:?}")))
}

fn parse(text: &str) -> PyResult<Decimal> {
    let parsed = if text.contains(['e', 'E']) { Decimal::from_scientific(text) } else { Decimal::from_str(text) };
    parsed.map_err(|e| PyValueError::new_err(format!("invalid decimal {text:?}: {e}")))
}

#[pyfunction]
fn minor_unit_exponent(currency: &str) -> PyResult<u32> {
    exponent(currency)
}

/// `Decimal(minor_units).scaleb(-exponent)` as text, scale preserved ("1.00").
#[pyfunction]
fn from_minor_units(minor_units: i128, currency: &str) -> PyResult<String> {
    let exp = exponent(currency)?;
    Decimal::try_from_i128_with_scale(minor_units, exp)
        .map(|d| d.to_string())
        .map_err(|e| PyValueError::new_err(format!("out of range: {e}")))
}

/// `Money.as_minor_units`: exact scale-up, error if it does not land on an integer.
#[pyfunction]
fn as_minor_units(amount: &str, currency: &str) -> PyResult<i128> {
    let exp = exponent(currency)?;
    let scaled = parse(amount)?
        .checked_mul(Decimal::from(10u64.pow(exp)))
        .ok_or_else(|| PyValueError::new_err("overflow"))?;
    if !scaled.fract().is_zero() {
        return Err(PyValueError::new_err(format!("{amount} does not scale cleanly to {exp} digits")));
    }
    scaled.trunc().to_i128().ok_or_else(|| PyValueError::new_err("overflow"))
}

/// `FXSnapshot.convert`: amount * rate, quantized half-even to the quote currency's minor units.
#[pyfunction]
fn fx_convert(amount: &str, rate: &str, quote_currency: &str) -> PyResult<String> {
    let exp = exponent(quote_currency)?;
    let product = parse(amount)?
        .checked_mul(parse(rate)?)
        .ok_or_else(|| PyValueError::new_err("overflow"))?;
    let mut rounded = product.round_dp_with_strategy(exp, RoundingStrategy::MidpointNearestEven);
    rounded.rescale(exp); // pad to the quote currency's digits, like Decimal.quantize
    let text = rounded.to_string();
    // Python keeps the sign of a negative product that rounds to zero ("-0.00").
    Ok(if product.is_sign_negative() && rounded.is_zero() { format!("-{text}") } else { text })
}

#[pymodule]
fn cheapwings_money_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(minor_unit_exponent, m)?)?;
    m.add_function(wrap_pyfunction!(from_minor_units, m)?)?;
    m.add_function(wrap_pyfunction!(as_minor_units, m)?)?;
    m.add_function(wrap_pyfunction!(fx_convert, m)?)?;
    Ok(())
}
