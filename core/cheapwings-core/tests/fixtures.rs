//! Shared fixtures generated from the Python reference (scripts/gen_core_fixtures.py).

use cheapwings_core::fingerprint::{fingerprint, isoformat, LocalInstant, Segment};
use cheapwings_core::fli::{airport_changes, cross_check, decode_page, filter_offers, search_url, tfs, FliLeg, FliOffer};
use cheapwings_core::locations::Catalog;
use cheapwings_core::money::{as_minor_units, from_minor_units, fx_convert};
use cheapwings_core::planning::{plan_search, RouteDate};
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
#[serde(untagged)]
enum PlanExpect {
    Combos(Vec<RouteDate>),
    Error { error: String },
}

#[derive(Deserialize)]
struct PlanCase {
    origins: Vec<String>,
    destinations: Vec<String>,
    from: String,
    through: String,
    max: u32,
    expect: PlanExpect,
}

#[derive(Deserialize)]
struct Fixtures {
    money: Vec<MoneyCase>,
    fingerprint: Vec<FingerprintCase>,
    ranking: Vec<RankingCase>,
    fli_tfs: Vec<TfsCase>,
    fli_pages: Vec<PageCase>,
    planning: Vec<PlanCase>,
    location_search: Vec<SearchCase>,
    location_major: Vec<MajorCase>,
}

#[derive(Deserialize)]
#[serde(untagged)]
enum SearchExpect {
    Ids(Vec<String>),
    Error { error: String },
}

#[derive(Deserialize)]
struct SearchCase {
    text: String,
    within: Option<String>,
    expect: SearchExpect,
}

#[derive(Deserialize)]
#[serde(untagged)]
enum MajorExpect {
    Resolved { codes: Vec<String>, rationale: String, definition: String },
    Error { error: String },
}

#[derive(Deserialize)]
struct MajorCase {
    kind: String,
    id: String,
    version: String,
    expect: MajorExpect,
}

const CATALOG: &str = concat!(env!("CARGO_MANIFEST_DIR"), "/../../backend/src/cheapwings/locations/catalog.json");

fn catalog() -> Catalog {
    Catalog::from_json(&std::fs::read_to_string(CATALOG).expect("catalog file")).expect("valid catalog")
}

fn leg(origin: &str, destination: &str, depart: &str, arrive: &str) -> FliLeg {
    FliLeg {
        origin: origin.into(),
        destination: destination.into(),
        airline: "GA".into(),
        flight_number: "1".into(),
        depart_local: depart.into(),
        arrive_local: arrive.into(),
    }
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
fn planning_matches_python() {
    let cases = fixtures().planning;
    for (i, c) in cases.iter().enumerate() {
        let got = plan_search(&c.origins, &c.destinations, &c.from, &c.through, c.max);
        match (&got, &c.expect) {
            (Ok(combos), PlanExpect::Combos(want)) => assert_eq!(combos, want, "case #{i}"),
            (Err(e), PlanExpect::Error { error }) => assert_eq!(e.code(), error, "case #{i}"),
            _ => panic!("case #{i}: got {got:?}"),
        }
    }
    assert_eq!(cases.len(), 66);
}

#[test]
fn planning_counts_leap_day() {
    let one = |c: &str| vec![c.to_string()];
    let combos = plan_search(&one("CGK"), &one("DPS"), "2028-02-28", "2028-03-01", 120).expect("plans");
    let dates: Vec<&str> = combos.iter().map(|c| c.date.as_str()).collect();
    assert_eq!(dates, ["2028-02-28", "2028-02-29", "2028-03-01"]);
}

#[test]
fn filter_offers_keeps_good_rows_and_explains_dropped_ones() {
    // Live CGK→HND page (2027-01-01) had 8 good rows and 2 without a currency token;
    // one bad row must not discard the whole page.
    let good = one_row_page("1250000");
    let no_token = one_row_page("4161210").replace("\"GgUaA0lEUg\"", "null");
    let mut page = decode_page(&good).expect("decodes");
    page.offers.extend(decode_page(&no_token).expect("decodes").offers);
    assert_eq!(page.offers[1].currency, None);

    let checked = filter_offers(&page, "CGK", "DPS", "2026-12-15", "IDR", None);
    assert_eq!(checked.offers.iter().map(|o| o.price.as_str()).collect::<Vec<_>>(), ["1250000"]);
    assert_eq!(checked.rejected, ["currency None"]);
    // The all-or-nothing check still reports the first mismatch.
    assert_eq!(cross_check(&page, "CGK", "DPS", "2026-12-15", "IDR").as_deref(), Some("currency None"));
}

#[test]
fn location_search_matches_python() {
    let cat = catalog();
    let cases = fixtures().location_search;
    for c in &cases {
        let got = cat.search(&c.text, c.within.as_deref());
        match (&got, &c.expect) {
            (Ok(found), SearchExpect::Ids(ids)) => {
                let got_ids: Vec<&str> = found.iter().take(15).map(|l| l.id.as_str()).collect();
                assert_eq!(got_ids, ids.iter().map(String::as_str).collect::<Vec<_>>(), "search {:?} within {:?}", c.text, c.within);
            }
            (Err(e), SearchExpect::Error { error }) => assert_eq!(e.code(), error, "search {:?}", c.text),
            _ => panic!("search {:?} within {:?}: got {got:?}", c.text, c.within),
        }
    }
    assert_eq!(cases.len(), 54);
}

#[test]
fn location_major_matches_python() {
    let cat = catalog();
    let cases = fixtures().location_major;
    for c in &cases {
        match (cat.resolve_major(&c.kind, &c.id, &c.version), &c.expect) {
            (Ok(r), MajorExpect::Resolved { codes, rationale, definition }) => {
                assert_eq!(&r.codes, codes, "{}", c.id);
                assert_eq!(&r.rationale, rationale);
                assert_eq!(&r.definition, definition);
                assert!(cat.has_major(&c.id));
            }
            (Err(e), MajorExpect::Error { error }) => assert_eq!(e.code(), error, "{} {} {}", c.kind, c.id, c.version),
            (got, _) => panic!("{} {}: got {got:?}", c.kind, c.id),
        }
    }
    assert_eq!(cases.len(), 14);
}

#[test]
fn catalog_rejects_inconsistent_data() {
    let base = |entities: &str, major: &str| {
        format!(r#"{{"version":"t","definition":"d","entities":[{entities}],"major":{{{major}}}}}"#)
    };
    let airport = r#"{"id":"airport:AAA","type":"airport","name":"A","country":"XX","country_name":"X","codes":["AAA"],"aliases":[],"code":"AAA"}"#;
    let city = r#"{"id":"metro:XX:AAA","type":"city","name":"C","country":"XX","country_name":"X","codes":["AAA"],"aliases":[]}"#;
    assert!(Catalog::from_json(&base(&format!("{airport},{city}"), r#""metro:XX:AAA":{"codes":["AAA"],"rationale":"r"}"#)).is_ok());
    assert!(Catalog::from_json(&base(&format!("{airport},{airport}"), "")).is_err(), "duplicate id");
    assert!(Catalog::from_json(&base(&format!("{airport},{city}"), r#""metro:XX:AAA":{"codes":["BBB"],"rationale":"r"}"#)).is_err(), "mapping code outside entity");
    assert!(Catalog::from_json(&base(&format!("{airport},{city}"), r#""airport:AAA":{"codes":["AAA"],"rationale":"r"}"#)).is_err(), "mapping on an airport");
}

#[test]
fn airport_lookup_has_timezone() {
    let cat = catalog();
    let hnd = cat.airport("HND").expect("HND");
    assert_eq!(hnd.timezone.as_deref(), Some("Asia/Tokyo"));
    assert_eq!(cat.airport("CGK").unwrap().timezone.as_deref(), Some("Asia/Jakarta"));
    assert!(cat.airport("ZZZZ").is_none());
    assert_eq!(cat.airports_of("metro:JP:TYO").unwrap().iter().map(|l| l.code.clone().unwrap()).collect::<Vec<_>>(), ["HND", "NRT"]);
}

#[test]
fn filter_offers_applies_max_stops() {
    let mut page = decode_page(&one_row_page("1250000")).expect("decodes");
    let nonstop = page.offers[0].clone();
    let mut one_stop = nonstop.clone();
    one_stop.legs = vec![leg("CGK", "SUB", "2026-12-15T06:05", "2026-12-15T07:30"), leg("SUB", "DPS", "2026-12-15T08:30", "2026-12-15T09:40")];
    page.offers = vec![nonstop, one_stop];
    let only_nonstop = filter_offers(&page, "CGK", "DPS", "2026-12-15", "IDR", Some(0));
    assert_eq!(only_nonstop.offers.len(), 1);
    assert_eq!(only_nonstop.rejected, ["stops 1 > 0"]);
    assert_eq!(filter_offers(&page, "CGK", "DPS", "2026-12-15", "IDR", Some(1)).offers.len(), 2);
    assert_eq!(filter_offers(&page, "CGK", "DPS", "2026-12-15", "IDR", None).offers.len(), 2);
}

#[test]
fn airport_changes_detects_nrt_hnd() {
    let offer = FliOffer {
        price: "1".into(),
        currency: Some("IDR".into()),
        legs: vec![leg("CGK", "NRT", "2026-12-15T06:00", "2026-12-15T15:00"), leg("HND", "ITM", "2026-12-15T18:00", "2026-12-15T19:10")],
    };
    assert_eq!(airport_changes(&offer), vec![("NRT".to_string(), "HND".to_string())]);
    let same = FliOffer { legs: vec![offer.legs[0].clone(), leg("NRT", "ITM", "x", "y")], ..offer };
    assert!(airport_changes(&same).is_empty());
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
