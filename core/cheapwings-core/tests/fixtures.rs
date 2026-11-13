//! Shared fixtures generated from the Python reference (scripts/gen_core_fixtures.py).

use cheapwings_core::fingerprint::{fingerprint, isoformat, LocalInstant, Segment};
use cheapwings_core::money::{as_minor_units, from_minor_units, fx_convert};
use cheapwings_core::ranking::{best_checked_deal, lowest_advertised, RankOffer};
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
struct FingerprintCase {
    segments: Vec<Segment>,
    expect: String,
}

#[derive(Deserialize)]
struct RankingCase {
    groups: Vec<Vec<RankOffer>>,
    best: Vec<String>,
    lowest: Vec<String>,
}

#[derive(Deserialize)]
struct Fixtures {
    money: Vec<MoneyCase>,
    fingerprint: Vec<FingerprintCase>,
    ranking: Vec<RankingCase>,
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
fn fingerprint_matches_python() {
    let cases = fixtures().fingerprint;
    let wrong: Vec<usize> = cases.iter().enumerate().filter(|(_, c)| fingerprint(&c.segments) != c.expect).map(|(i, _)| i).collect();
    assert!(wrong.is_empty(), "{} wrong fingerprints, first case #{:?}", wrong.len(), wrong.first());
    assert_eq!(cases.len(), 500);
}

#[test]
fn ranking_matches_python() {
    let cases = fixtures().ranking;
    let wrong: Vec<usize> = cases
        .iter()
        .enumerate()
        .filter(|(_, c)| best_checked_deal(&c.groups) != c.best || lowest_advertised(&c.groups) != c.lowest)
        .map(|(i, _)| i)
        .collect();
    assert!(wrong.is_empty(), "{} wrong rankings, first case #{:?}", wrong.len(), wrong.first());
    assert_eq!(cases.len(), 300);
}

#[test]
fn isoformat_matches_python_shapes() {
    let at = |us, offset| LocalInstant { y: 2026, mo: 12, d: 5, h: 6, mi: 5, s: 0, us, offset };
    assert_eq!(isoformat(&at(500, 25200)), "2026-12-05T06:05:00.000500+07:00");
    assert_eq!(isoformat(&at(0, -12600)), "2026-12-05T06:05:00-03:30");
    assert_eq!(isoformat(&at(0, 20700)), "2026-12-05T06:05:00+05:45");
    assert_eq!(isoformat(&at(0, 0)), "2026-12-05T06:05:00+00:00");
}

#[test]
fn fx_negative_zero_keeps_sign() {
    assert_eq!(fx_convert("-0.004", "1", "USD").as_deref(), Ok("-0.00"));
    assert_eq!(fx_convert("-0.4", "1", "IDR").as_deref(), Ok("-0"));
}
