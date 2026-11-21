//! P7.2 discovery contract: hand-specified cases in contracts/fixtures/core/discovery_fixtures.json.

use cheapwings_core::discovery::{
    select_discovery_plan, DiscoveryCounts, DiscoveryObservation, DiscoveryPlan, DiscoveryQuery,
    FxRate, SelectedLead,
};
use serde::Deserialize;

const FIXTURES: &str = concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/../../contracts/fixtures/core/discovery_fixtures.json"
);

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Expect {
    selected: Option<Vec<SelectedLead>>,
    counts: Option<DiscoveryCounts>,
    error: Option<String>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Case {
    name: String,
    query: DiscoveryQuery,
    fx: Vec<FxRate>,
    max_route_dates: u32,
    observations: Vec<DiscoveryObservation>,
    expect: Expect,
}

#[derive(Deserialize)]
struct Fixtures {
    cases: Vec<Case>,
}

fn cases() -> Vec<Case> {
    let text = std::fs::read_to_string(FIXTURES).expect("discovery fixture readable");
    serde_json::from_str::<Fixtures>(&text)
        .expect("discovery fixture parses")
        .cases
}

#[test]
fn fixture_parses() {
    let cases = cases();
    assert!(
        cases.len() >= 14,
        "expected all P7.2 cases, got {}",
        cases.len()
    );
    for case in &cases {
        let e = &case.expect;
        match (&e.error, &e.selected, &e.counts) {
            (Some(_), None, None) => {}
            (None, Some(selected), Some(c)) => {
                let total = c.selected
                    + c.invalid
                    + c.hidden_city
                    + c.out_of_window
                    + c.undated
                    + c.no_fx
                    + c.over_budget
                    + c.superseded
                    + c.capped;
                assert_eq!(
                    total, c.observed,
                    "{}: counts must sum to observed",
                    case.name
                );
                assert_eq!(
                    c.observed as usize,
                    case.observations.len(),
                    "{}: observed",
                    case.name
                );
                assert_eq!(
                    c.selected as usize,
                    selected.len(),
                    "{}: selected",
                    case.name
                );
                assert!(
                    selected.len() as u32 <= case.max_route_dates,
                    "{}: cap",
                    case.name
                );
            }
            _ => panic!(
                "{}: expect is either {{error}} or {{selected, counts}}",
                case.name
            ),
        }
    }
}

fn check(case: &Case) {
    let got = select_discovery_plan(
        &case.observations,
        &case.query,
        &case.fx,
        case.max_route_dates,
    );
    match (&case.expect.error, got) {
        (Some(code), Err(e)) => assert_eq!(e.code(), code, "{}", case.name),
        (Some(code), Ok(plan)) => panic!("{}: expected error {code}, got {plan:?}", case.name),
        (None, Err(e)) => panic!("{}: unexpected error {e}", case.name),
        (None, Ok(plan)) => assert_eq!(
            plan,
            DiscoveryPlan {
                selected: case.expect.selected.clone().unwrap(),
                counts: case.expect.counts.clone().unwrap(),
            },
            "{}",
            case.name
        ),
    }
}

fn check_named(name: &str) {
    let cases = cases();
    check(
        cases
            .iter()
            .find(|c| c.name == name)
            .expect("named case exists"),
    );
}

#[test]
fn fixture_cases() {
    cases().iter().for_each(check);
}

#[test]
fn normalizes_codes_like_search() {
    check_named("normalizes_codes_like_search");
}

#[test]
fn unknown_currency_is_no_fx() {
    check_named("unknown_currency_is_no_fx");
}

#[test]
fn huge_amount_is_invalid() {
    check_named("huge_amount_is_invalid");
}

#[test]
fn empty_input_is_empty_plan() {
    check_named("empty_input_is_empty_plan");
}

#[test]
fn window_is_inclusive() {
    check_named("window_is_inclusive");
}
