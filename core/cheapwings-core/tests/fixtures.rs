//! Shared fixtures generated from the Python reference (scripts/gen_core_fixtures.py).

use cheapwings_core::fingerprint::{fingerprint, isoformat, LocalInstant, Segment};
use cheapwings_core::fli::{cross_check, decode_page, search_url, tfs, FliOffer};
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
struct TfsCase {
    origin: String,
    destination: String,
    date: String,
    expect: String,
}

#[derive(Deserialize)]
struct PageExpect {
    offers: Option<Vec<FliOffer>>,
    unpriced: Option<u32>,
    error: Option<String>,
}

#[derive(Deserialize)]
struct PageCase {
    html: String,
    expect: PageExpect,
}

#[derive(Deserialize)]
struct Fixtures {
    money: Vec<MoneyCase>,
    fingerprint: Vec<FingerprintCase>,
    ranking: Vec<RankingCase>,
    fli_tfs: Vec<TfsCase>,
    fli_pages: Vec<PageCase>,
}

/// One priced CGK→DPS row on 2026-12-15 in the ds:1 layout, price spliced in as raw JSON.
fn one_row_page(price: &str) -> String {
    let mut leg = vec!["null".to_string(); 23];
    leg[3] = "\"CGK\"".into();
    leg[6] = "\"DPS\"".into();
    leg[8] = "[6,5]".into();
    leg[10] = "[9,0]".into();
    leg[11] = "115".into();
    leg[20] = "[2026,12,15]".into();
    leg[21] = "[2026,12,15]".into();
    leg[22] = "[\"GA\",\"402\",null]".into();
    let detail = format!("[null,null,[[{}]],null,null,null,null,null,null,115]", leg.join(","));
    let data = format!("[null,null,[[[{detail},[[null,{price}],\"GgUaA0lEUg\"]]]],null]");
    format!("<script>AF_initDataCallback({{key: 'ds:1', hash: '2', data:{data}, sideChannel: {{}}}});</script>")
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
fn fli_tfs_matches_python() {
    let cases = fixtures().fli_tfs;
    for c in &cases {
        assert_eq!(tfs(&c.origin, &c.destination, &c.date), c.expect, "{} {} {}", c.origin, c.destination, c.date);
    }
    assert_eq!(cases.len(), 50);
    assert_eq!(
        search_url("CGK", "DPS", "2026-12-15", "IDR", "ID"),
        "https://www.google.com/travel/flights?tfs=CBwQAhoeEgoyMDI2LTEyLTE1agcIARIDQ0dLcgcIARIDRFBTQAFIAXABmAEC&hl=en&gl=ID&curr=IDR"
    );
}

#[test]
fn fli_pages_match_python() {
    let cases = fixtures().fli_pages;
    for (i, c) in cases.iter().enumerate() {
        match (decode_page(&c.html), &c.expect.error) {
            (Ok(page), None) => {
                assert_eq!(Some(&page.offers), c.expect.offers.as_ref(), "page #{i} offers");
                assert_eq!(Some(page.unpriced), c.expect.unpriced, "page #{i} unpriced");
            }
            (Err(e), Some(code)) => assert_eq!(e.code(), code, "page #{i} error"),
            (got, want) => panic!("page #{i}: got {got:?}, want error {want:?}"),
        }
    }
    assert_eq!(cases.len(), 45);
}

#[test]
fn fli_price_keeps_trailing_zero() {
    let page = decode_page(&one_row_page("1234.50")).expect("decodes");
    assert_eq!(page.offers[0].price, "1234.50");
    assert_eq!(page.offers[0].currency.as_deref(), Some("IDR"));
}

#[test]
fn fli_cross_check_catches_wrong_date() {
    let page = decode_page(&one_row_page("1250000")).expect("decodes");
    assert_eq!(cross_check(&page, "CGK", "DPS", "2026-12-15", "IDR"), None);
    assert!(cross_check(&page, "CGK", "DPS", "2026-12-16", "IDR").is_some());
    assert!(cross_check(&page, "CGK", "SUB", "2026-12-15", "IDR").is_some());
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
