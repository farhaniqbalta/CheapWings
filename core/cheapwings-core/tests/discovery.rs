//! P7.2 discovery contract: hand-specified cases in contracts/fixtures/core/discovery_fixtures.json.

use cheapwings_core::discovery::{
    DiscoveryCounts, DiscoveryObservation, DiscoveryQuery, FxRate, SelectedLead,
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
#[allow(dead_code)] // query and fx are consumed by select_discovery_plan (P7.3)
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
    serde_json::from_str::<Fixtures>(&text).expect("discovery fixture parses").cases
}

#[test]
fn fixture_parses() {
    let cases = cases();
    assert!(cases.len() >= 14, "expected all P7.2 cases, got {}", cases.len());
    for case in &cases {
        let e = &case.expect;
        match (&e.error, &e.selected, &e.counts) {
            (Some(_), None, None) => {}
            (None, Some(selected), Some(c)) => {
                let total = c.selected + c.invalid + c.hidden_city + c.out_of_window + c.undated
                    + c.no_fx + c.over_budget + c.superseded + c.capped;
                assert_eq!(total, c.observed, "{}: counts must sum to observed", case.name);
                assert_eq!(c.observed as usize, case.observations.len(), "{}: observed", case.name);
                assert_eq!(c.selected as usize, selected.len(), "{}: selected", case.name);
                assert!(selected.len() as u32 <= case.max_route_dates, "{}: cap", case.name);
            }
            _ => panic!("{}: expect is either {{error}} or {{selected, counts}}", case.name),
        }
    }
}
