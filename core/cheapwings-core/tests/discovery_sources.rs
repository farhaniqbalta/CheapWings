//! P7.4 discovery sources: Skiplagged anywhere parsing and the discovery call plan
//! (contracts/fixtures/core/discovery_sources_fixtures.json, scripts/gen_discovery_sources_fixtures.py).

use cheapwings_core::discovery::{DiscoveryObservation, DiscoveryQuery, FxRate};
use cheapwings_core::discovery_sources::{
    discovery_calls, skiplagged_anywhere, DiscoveryCall, MAX_DISCOVERY_CALLS,
};
use serde::Deserialize;

const FIXTURES: &str = concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/../../contracts/fixtures/core/discovery_sources_fixtures.json"
);

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct AnywhereExpect {
    observations: Option<Vec<DiscoveryObservation>>,
    count: Option<usize>,
    first: Option<Option<DiscoveryObservation>>,
    unpriced: Option<u32>,
    fx: Option<Vec<FxRate>>,
    error: Option<String>,
}

#[derive(Deserialize)]
struct AnywhereCase {
    name: String,
    rpc_json: String,
    origin: String,
    depart: String,
    fetched_at: String,
    expect: AnywhereExpect,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct CallsExpect {
    calls: Option<Vec<DiscoveryCall>>,
    count: Option<usize>,
    error: Option<String>,
}

#[derive(Deserialize)]
struct CallsCase {
    name: String,
    query: DiscoveryQuery,
    expect: CallsExpect,
}

#[derive(Deserialize)]
struct Fixtures {
    anywhere: Vec<AnywhereCase>,
    discovery_calls: Vec<CallsCase>,
}

fn fixtures() -> Fixtures {
    serde_json::from_str(&std::fs::read_to_string(FIXTURES).expect("fixture readable"))
        .expect("fixture parses")
}

#[test]
fn anywhere_fixture_cases() {
    let cases = fixtures().anywhere;
    assert_eq!(cases.len(), 10);
    for c in &cases {
        let got = skiplagged_anywhere(&c.rpc_json, &c.origin, &c.depart, &c.fetched_at);
        let e = &c.expect;
        if let Some(code) = &e.error {
            assert_eq!(
                got.err().map(|e| e.code()),
                Some(code.as_str()),
                "{}",
                c.name
            );
            continue;
        }
        let page = got.unwrap_or_else(|err| panic!("{}: {err}", c.name));
        if let Some(all) = &e.observations {
            assert_eq!(&page.observations, all, "{}", c.name);
        }
        if let Some(count) = e.count {
            assert_eq!(page.observations.len(), count, "{}", c.name);
        }
        if let Some(first) = &e.first {
            assert_eq!(page.observations.first(), first.as_ref(), "{}", c.name);
        }
        assert_eq!(Some(page.unpriced), e.unpriced, "{}", c.name);
        assert_eq!(Some(&page.fx), e.fx.as_ref(), "{}", c.name);
    }
}

#[test]
fn discovery_call_cases() {
    assert_eq!(MAX_DISCOVERY_CALLS, 31);
    for c in fixtures().discovery_calls {
        match (discovery_calls(&c.query), &c.expect) {
            (
                Err(err),
                CallsExpect {
                    error: Some(code), ..
                },
            ) => assert_eq!(err.code(), code, "{}", c.name),
            (
                Ok(calls),
                CallsExpect {
                    calls: Some(want), ..
                },
            ) => assert_eq!(&calls, want, "{}", c.name),
            (Ok(calls), CallsExpect { count: Some(n), .. }) => {
                assert_eq!(calls.len(), *n, "{}", c.name)
            }
            (got, _) => panic!("{}: unexpected {got:?}", c.name),
        }
    }
}
