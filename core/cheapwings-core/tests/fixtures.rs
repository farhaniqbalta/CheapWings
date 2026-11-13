//! Shared fixtures generated from the Python reference (scripts/gen_core_fixtures.py).

use cheapwings_core::money::{as_minor_units, from_minor_units, fx_convert};
use serde::Deserialize;

const FIXTURES: &str = concat!(env!("CARGO_MANIFEST_DIR"), "/../../contracts/fixtures/core/core_fixtures.json");

#[derive(Deserialize)]
struct MoneyCase {
    op: String,
    amount: Option<String>,
    rate: Option<String>,
    minor: Option<String>,
    currency: String,
    expect: Option<String>,
}

#[derive(Deserialize)]
struct Fixtures {
    money: Vec<MoneyCase>,
}

fn fixtures() -> Fixtures {
    serde_json::from_str(&std::fs::read_to_string(FIXTURES).expect("fixture file")).expect("fixture json")
}

fn money_result(c: &MoneyCase) -> Option<String> {
    match c.op.as_str() {
        "fx" => fx_convert(c.amount.as_deref()?, c.rate.as_deref()?, &c.currency).ok(),
        "from_minor" => from_minor_units(c.minor.as_deref()?.parse().ok()?, &c.currency).ok(),
        "as_minor" => as_minor_units(c.amount.as_deref()?, &c.currency).ok().map(|v| v.to_string()),
        other => panic!("unknown money op {other}"),
    }
}

#[test]
fn money_matches_python() {
    let cases = fixtures().money;
    let failures: Vec<String> = cases
        .iter()
        .filter_map(|c| {
            let got = money_result(c);
            (got != c.expect).then(|| format!("{} {:?} {:?} {}: got {got:?} want {:?}", c.op, c.amount, c.minor, c.currency, c.expect))
        })
        .collect();
    assert!(failures.is_empty(), "{} failures, first: {:?}", failures.len(), failures.first());
    assert_eq!(cases.len(), 3006);
}

#[test]
fn fx_negative_zero_keeps_sign() {
    assert_eq!(fx_convert("-0.004", "1", "USD").as_deref(), Ok("-0.00"));
    assert_eq!(fx_convert("-0.4", "1", "IDR").as_deref(), Ok("-0"));
}
