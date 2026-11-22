//! P7.4: Discover searches in the iPad store (schema v3).

use cheapwings_core::discovery::{DiscoveryObservation, FxRate};
use cheapwings_core::planning::RouteDate;
use cheapwings_store::{DiscoverySnapshot, Store, StoreError, StoredRequest, WorkItem};

fn open(dir: &tempfile::TempDir) -> Store {
    Store::open(dir.path().join("searches.sqlite").to_str().unwrap()).expect("opens")
}

fn discover_request() -> StoredRequest {
    StoredRequest {
        origins: vec!["CGK".into()],
        destinations: vec![],
        date_from: "2027-03-01".into(),
        date_through: "2027-03-02".into(),
        currency: "IDR".into(),
        max_stops: None,
        origin_majors: vec![],
        destination_majors: vec![],
        providers: vec!["fli".into(), "skiplagged".into()],
        kind: "discover".into(),
        budget: Some("1500000".into()),
    }
}

fn observation(dest: &str, amount: &str) -> DiscoveryObservation {
    DiscoveryObservation {
        origin: "CGK".into(),
        destination: dest.into(),
        departure_date: Some("2027-03-01".into()),
        amount: amount.into(),
        currency: "USD".into(),
        source_id: "skiplagged".into(),
        observed_at: None,
        fetched_at: "2027-02-20T00:00:00Z".into(),
        price_kind: "indicative".into(),
        hidden_city: "no".into(),
        source_reference: None,
    }
}

fn snapshot() -> DiscoverySnapshot {
    DiscoverySnapshot {
        observations: vec![observation("DPS", "46"), observation("SIN", "58.5")],
        fx: vec![FxRate {
            currency: "USD".into(),
            rate: "16000".into(),
        }],
        calls_planned: 2,
        calls_failed: 1,
        unpriced: 3,
    }
}

fn items() -> Vec<WorkItem> {
    ["fli", "skiplagged"]
        .iter()
        .map(|p| WorkItem {
            provider: (*p).into(),
            route_date: RouteDate {
                origin: "CGK".into(),
                destination: "DPS".into(),
                date: "2027-03-01".into(),
            },
        })
        .collect()
}

#[test]
fn discovery_starts_without_items() {
    let dir = tempfile::tempdir().unwrap();
    let store = open(&dir);
    let id = store.create_discovery(&discover_request(), 10).unwrap();
    let latest = store.latest().unwrap().unwrap();
    assert_eq!(latest.id, id);
    assert_eq!(latest.stage.as_deref(), Some("discovering"));
    assert_eq!(latest.request, discover_request());
    assert!(latest.combos.is_empty());
    assert_eq!(latest.discovery, None);
}

#[test]
fn latest_returns_observations() {
    let dir = tempfile::tempdir().unwrap();
    let store = open(&dir);
    let id = store.create_discovery(&discover_request(), 10).unwrap();
    store
        .commit_discovery(id, &snapshot(), &items(), 20)
        .unwrap();
    let latest = store.latest().unwrap().unwrap();
    assert_eq!(latest.stage.as_deref(), Some("checking"));
    assert_eq!(latest.discovery, Some(snapshot()));
    assert_eq!(latest.combos.len(), 2);
    assert_eq!(store.pending(id).unwrap().len(), 2);
    assert_eq!(latest.updated_at_ms, 20);
}

#[test]
fn commit_discovery_is_once() {
    let dir = tempfile::tempdir().unwrap();
    let store = open(&dir);
    let id = store.create_discovery(&discover_request(), 10).unwrap();
    store
        .commit_discovery(id, &snapshot(), &items(), 20)
        .unwrap();
    let again = store.commit_discovery(id, &snapshot(), &items(), 30);
    assert_eq!(again, Err(StoreError::AlreadyCommitted(id)));
    assert_eq!(again.unwrap_err().code(), "already_committed");
    let latest = store.latest().unwrap().unwrap();
    assert_eq!(latest.combos.len(), 2);
    assert_eq!(latest.discovery.unwrap().observations.len(), 2);
}

#[test]
fn search_cannot_be_committed_as_discovery() {
    let dir = tempfile::tempdir().unwrap();
    let store = open(&dir);
    let mut request = discover_request();
    request.kind = String::new();
    let id = store.create_search(&request, &items(), 10).unwrap();
    assert_eq!(
        store.commit_discovery(id, &snapshot(), &[], 20),
        Err(StoreError::AlreadyCommitted(id))
    );
    assert_eq!(store.latest().unwrap().unwrap().stage, None);
}

#[test]
fn commit_to_unknown_search_changes_nothing() {
    let dir = tempfile::tempdir().unwrap();
    let store = open(&dir);
    let id = store.create_discovery(&discover_request(), 10).unwrap();
    assert_eq!(
        store.commit_discovery(id + 1, &snapshot(), &items(), 20),
        Err(StoreError::NotFound(id + 1))
    );
    let latest = store.latest().unwrap().unwrap();
    assert_eq!(latest.stage.as_deref(), Some("discovering"));
    assert!(latest.combos.is_empty());
    assert_eq!(latest.discovery, None);
}

#[test]
fn empty_commit_records_unavailable_discovery() {
    let dir = tempfile::tempdir().unwrap();
    let store = open(&dir);
    let id = store.create_discovery(&discover_request(), 10).unwrap();
    let failed = DiscoverySnapshot {
        observations: vec![],
        fx: vec![],
        calls_planned: 2,
        calls_failed: 2,
        unpriced: 0,
    };
    store.commit_discovery(id, &failed, &[], 20).unwrap();
    let latest = store.latest().unwrap().unwrap();
    assert_eq!(latest.stage.as_deref(), Some("checking"));
    assert_eq!(latest.discovery, Some(failed));
    assert!(latest.combos.is_empty());
}

#[test]
fn v2_file_migrates() {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("searches.sqlite");
    {
        // The P5.4 (v2) schema with one finished Skiplagged search.
        let conn = rusqlite::Connection::open(&path).unwrap();
        conn.execute_batch(
            "CREATE TABLE searches (id INTEGER PRIMARY KEY AUTOINCREMENT, request TEXT NOT NULL, created_at_ms INTEGER NOT NULL, updated_at_ms INTEGER NOT NULL, stop_reason TEXT, provider_stops TEXT);
             CREATE TABLE combos (search_id INTEGER NOT NULL REFERENCES searches(id) ON DELETE CASCADE, idx INTEGER NOT NULL, origin TEXT NOT NULL, destination TEXT NOT NULL, date TEXT NOT NULL, status TEXT NOT NULL, code TEXT, finished_at_ms INTEGER, provider TEXT NOT NULL DEFAULT 'fli', PRIMARY KEY (search_id, idx));
             CREATE TABLE offers (search_id INTEGER NOT NULL REFERENCES searches(id) ON DELETE CASCADE, combo_idx INTEGER NOT NULL, offer_idx INTEGER NOT NULL, price TEXT NOT NULL, currency TEXT, legs TEXT NOT NULL, fetched_at_ms INTEGER NOT NULL, offer_json TEXT, PRIMARY KEY (search_id, combo_idx, offer_idx));
             CREATE TABLE hidden (search_id INTEGER NOT NULL REFERENCES searches(id) ON DELETE CASCADE, combo_idx INTEGER NOT NULL, reason TEXT NOT NULL, count INTEGER NOT NULL, PRIMARY KEY (search_id, combo_idx, reason));
             PRAGMA user_version = 2;",
        )
        .unwrap();
        let request = r#"{"origins":["CGK"],"destinations":["DPS"],"date_from":"2026-12-15","date_through":"2026-12-15","currency":"IDR","providers":["skiplagged"]}"#;
        conn.execute("INSERT INTO searches (request, created_at_ms, updated_at_ms, stop_reason) VALUES (?1, 1, 2, 'finished')", [request]).unwrap();
        conn.execute("INSERT INTO combos VALUES (1, 0, 'CGK', 'DPS', '2026-12-15', 'done', NULL, 2, 'skiplagged')", []).unwrap();
    }
    let store = Store::open(path.to_str().unwrap()).expect("migrates");
    let latest = store.latest().unwrap().unwrap();
    assert_eq!(latest.stage, None);
    assert_eq!(latest.discovery, None);
    assert_eq!(latest.request.kind, "");
    assert_eq!(latest.request.budget, None);
    assert_eq!(latest.combos[0].provider, "skiplagged");
    drop(store);
    let again = Store::open(path.to_str().unwrap()).expect("reopens");
    assert_eq!(again.latest().unwrap().unwrap().combos.len(), 1);
}
