//! Thin PyO3 wrappers over the `cheapwings-core` crate. Values cross as text; every error
//! is a `ValueError` whose message starts with `unknown_currency:` for unknown currencies.

use engine::money::{self, MoneyError};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

fn to_py(err: MoneyError) -> PyErr {
    PyValueError::new_err(err.to_string())
}

#[pyfunction]
fn minor_unit_exponent(currency: &str) -> PyResult<u32> {
    money::minor_unit_exponent(currency).map_err(to_py)
}

#[pyfunction]
fn from_minor_units(minor: i128, currency: &str) -> PyResult<String> {
    money::from_minor_units(minor, currency).map_err(to_py)
}

#[pyfunction]
fn as_minor_units(amount: &str, currency: &str) -> PyResult<i128> {
    money::as_minor_units(amount, currency).map_err(to_py)
}

#[pyfunction]
fn fx_convert(amount: &str, rate: &str, quote_currency: &str) -> PyResult<String> {
    money::fx_convert(amount, rate, quote_currency).map_err(to_py)
}

#[pymodule]
fn cheapwings_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(minor_unit_exponent, m)?)?;
    m.add_function(wrap_pyfunction!(from_minor_units, m)?)?;
    m.add_function(wrap_pyfunction!(as_minor_units, m)?)?;
    m.add_function(wrap_pyfunction!(fx_convert, m)?)?;
    Ok(())
}
