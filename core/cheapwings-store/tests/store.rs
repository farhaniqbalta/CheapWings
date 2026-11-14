use cheapwings_core::fli::{FliLeg, FliOffer};
use cheapwings_core::planning::RouteDate;
use cheapwings_core::skiplagged::{fli_source_offer, SourceOffer};
use cheapwings_store::{ComboStatus, Store, StoreError, StoredRequest, WorkItem};

fn request() -> StoredRequest {
    StoredRequest {
        origins: vec!["CGK".into()],
        destinations: vec!["DPS".into()],
        date_from: "2026-12-15".into(),
        date_through: "2026-12-17".into(),
        currency: "IDR".into(),
        max_stops: Some(1),
        origin_majors: vec![],
        destination_majors: vec!["metro:JP:TYO".into(), "metro:JP:OSA".into()],
        providers: vec!["fli".into()],
    }
}

fn route(date: &str) -> RouteDate {
    RouteDate { origin: "CGK".into(), destination: "DPS".into(), date: date.into() }
}

/// Fli work items for 15–17 Dec.
fn combos() -> Vec<WorkItem> {
    ["2026-12-15", "2026-12-16", "2026-12-17"].iter().map(|d| WorkItem { provider: "fli".into(), route_date: route(d) }).collect()
}

fn fli_offer(price: &str) -> FliOffer {
    FliOffer {
        price: price.into(),
        currency: Some("IDR".into()),
        legs: vec![FliLeg {
            origin: "CGK".into(),
            destination: "DPS".into(),
            airline: "GA".into(),
            flight_number: "402".into(),
            depart_local: "2026-12-15T06:05".into(),
            arrive_local: "2026-12-15T09:00".into(),
        }],
    }
}

fn offer(price: &str) -> SourceOffer {
    fli_source_offer(&fli_offer(price), "", "IDR")
}

fn skiplagged_offer() -> SourceOffer {
    SourceOffer {
        provider: "skiplagged".into(),
        id: "abc".into(),
        origin: "CGK".into(),
        destination: "DPS".into(),
        depart_local: "2026-12-15T07:00".into(),
        arrive_local: "2026-12-15T09:55".into(),
        minutes: Some(115),
        stops: 0,
        carriers: vec!["Garuda Indonesia".into()],
        legs: vec![],
        price_original: "71.50".into(),
        currency_original: "USD".into(),
        price_comparable: Some("1294772".into()),
        fx: None,
        link: Some("https://skiplagged.com/flights/CGK/DPS/2026-12-15".into()),
        hidden_city: "no".into(),
    }
}

fn open(dir: &tempfile::TempDir) -> Store {
    Store::open(dir.path().join("searches.sqlite").to_str().unwrap()).expect("opens")
}

#[test]
fn round_trip_keeps_offers_exactly() {
    let dir = tempfile::tempdir().unwrap();
    let store = open(&dir);
    let id = store.create_search(&request(), &combos(), 1_000).unwrap();
    store.finish_combo(id, 0, &[offer("1234.50")], &["currency None".into()], None, 2_000).unwrap();
    let latest = store.latest().unwrap().expect("a search");
    assert_eq!(latest.id, id);
    assert_eq!(latest.request, request());
    assert_eq!(latest.offers.len(), 1);
    assert_eq!(latest.offers[0].offer, offer("1234.50"));
    assert_eq!(latest.offers[0].fetched_at_ms, 2_000);
    assert_eq!(latest.hidden, vec![("currency None".to_string(), 1)]);
    assert_eq!(latest.combos[0].status, ComboStatus::Done);
    assert_eq!(latest.combos[0].provider, "fli");
    assert_eq!(latest.combos[1].status, ComboStatus::Pending);
}

#[test]
fn finish_combo_is_idempotent() {
    let dir = tempfile::tempdir().unwrap();
    let store = open(&dir);
    let id = store.create_search(&request(), &combos(), 1_000).unwrap();
    store.finish_combo(id, 1, &[offer("1"), offer("2")], &[], None, 2_000).unwrap();
    store.finish_combo(id, 1, &[offer("3")], &[], None, 3_000).unwrap();
    let latest = store.latest().unwrap().unwrap();
    assert_eq!(latest.offers.iter().map(|o| o.offer.price_original.as_str()).collect::<Vec<_>>(), ["3"]);
}

#[test]
fn failed_combo_keeps_its_code() {
    let dir = tempfile::tempdir().unwrap();
    let store = open(&dir);
    let id = store.create_search(&request(), &combos(), 1_000).unwrap();
    store.finish_combo(id, 2, &[], &[], Some("cross_check: currency None"), 2_000).unwrap();
    let combo = &store.latest().unwrap().unwrap().combos[2];
    assert_eq!(combo.status, ComboStatus::Failed);
    assert_eq!(combo.code.as_deref(), Some("cross_check: currency None"));
    assert_eq!(combo.finished_at_ms, Some(2_000));
}

#[test]
fn pending_lists_unfinished_in_order() {
    let dir = tempfile::tempdir().unwrap();
    let store = open(&dir);
    let id = store.create_search(&request(), &combos(), 1_000).unwrap();
    store.finish_combo(id, 1, &[offer("1")], &[], None, 2_000).unwrap();
    let pending: Vec<u32> = store.pending(id).unwrap().iter().map(|c| c.index).collect();
    assert_eq!(pending, [0, 2]);
    assert_eq!(store.pending(id).unwrap()[1].route_date.date, "2026-12-17");
}

#[test]
fn stop_reason_round_trip() {
    let dir = tempfile::tempdir().unwrap();
    let store = open(&dir);
    let id = store.create_search(&request(), &combos(), 1_000).unwrap();
    store.set_stopped(id, "blocked:www.google.com/sorry/index", 5_000).unwrap();
    let latest = store.latest().unwrap().unwrap();
    assert_eq!(latest.stop_reason.as_deref(), Some("blocked:www.google.com/sorry/index"));
    assert_eq!(latest.updated_at_ms, 5_000);
    store.clear_stopped(id).unwrap();
    assert_eq!(store.latest().unwrap().unwrap().stop_reason, None);
}

#[test]
fn prunes_to_newest_ten() {
    let dir = tempfile::tempdir().unwrap();
    let store = open(&dir);
    let ids: Vec<i64> = (0..12).map(|i| store.create_search(&request(), &combos(), i).unwrap()).collect();
    assert_eq!(store.search_count().unwrap(), 10);
    assert_eq!(store.latest().unwrap().unwrap().id, ids[11]);
    assert!(matches!(store.pending(ids[0]), Err(StoreError::NotFound(_))));
}

#[test]
fn reopen_after_close_sees_data() {
    let dir = tempfile::tempdir().unwrap();
    let id = {
        let store = open(&dir);
        let id = store.create_search(&request(), &combos(), 1_000).unwrap();
        store.finish_combo(id, 0, &[offer("1250000")], &[], None, 2_000).unwrap();
        id
    }; // dropped mid-search: simulates the app being killed
    let latest = open(&dir).latest().unwrap().unwrap();
    assert_eq!(latest.id, id);
    assert_eq!(latest.offers[0].offer.price_original, "1250000");
    assert_eq!(latest.combos.iter().filter(|c| c.status == ComboStatus::Pending).count(), 2);
}

#[test]
fn corrupt_file_reports_open_error() {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("searches.sqlite");
    std::fs::write(&path, b"this is not a sqlite database, just garbage bytes......").unwrap();
    assert!(matches!(Store::open(path.to_str().unwrap()), Err(StoreError::Open(_))));
}

#[test]
fn empty_store_has_no_latest() {
    let dir = tempfile::tempdir().unwrap();
    assert!(open(&dir).latest().unwrap().is_none());
}

// ---- P5.4: providers ----

#[test]
fn work_items_keep_their_provider_and_neutral_offers() {
    let dir = tempfile::tempdir().unwrap();
    let store = open(&dir);
    let items = vec![
        WorkItem { provider: "fli".into(), route_date: route("2026-12-15") },
        WorkItem { provider: "skiplagged".into(), route_date: route("2026-12-15") },
    ];
    let id = store.create_search(&StoredRequest { providers: vec!["fli".into(), "skiplagged".into()], ..request() }, &items, 1_000).unwrap();
    store.finish_combo(id, 1, &[skiplagged_offer()], &[], None, 2_000).unwrap();
    let latest = store.latest().unwrap().unwrap();
    assert_eq!(latest.combos.iter().map(|c| c.provider.as_str()).collect::<Vec<_>>(), ["fli", "skiplagged"]);
    assert_eq!(latest.offers[0].combo_index, 1);
    assert_eq!(latest.offers[0].offer, skiplagged_offer());
    assert_eq!(store.pending(id).unwrap().iter().map(|c| c.provider.as_str()).collect::<Vec<_>>(), ["fli"]);
}

#[test]
fn provider_stops_round_trip() {
    let dir = tempfile::tempdir().unwrap();
    let store = open(&dir);
    let id = store.create_search(&request(), &combos(), 1_000).unwrap();
    store.set_provider_stopped(id, "fli", "rate_limited", 5_000).unwrap();
    store.set_provider_stopped(id, "skiplagged", "blocked:http_403", 6_000).unwrap();
    let latest = store.latest().unwrap().unwrap();
    assert_eq!(latest.provider_stops, vec![("fli".to_string(), "rate_limited".to_string()), ("skiplagged".to_string(), "blocked:http_403".to_string())]);
    store.clear_stopped(id).unwrap();
    assert!(store.latest().unwrap().unwrap().provider_stops.is_empty());
}

#[test]
fn version_one_database_migrates_in_place() {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("searches.sqlite");
    {
        // The P5.3–P5.8 schema with one Fli search half done.
        let conn = rusqlite::Connection::open(&path).unwrap();
        conn.execute_batch(
            "CREATE TABLE searches (id INTEGER PRIMARY KEY AUTOINCREMENT, request TEXT NOT NULL, created_at_ms INTEGER NOT NULL, updated_at_ms INTEGER NOT NULL, stop_reason TEXT);
             CREATE TABLE combos (search_id INTEGER NOT NULL REFERENCES searches(id) ON DELETE CASCADE, idx INTEGER NOT NULL, origin TEXT NOT NULL, destination TEXT NOT NULL, date TEXT NOT NULL, status TEXT NOT NULL, code TEXT, finished_at_ms INTEGER, PRIMARY KEY (search_id, idx));
             CREATE TABLE offers (search_id INTEGER NOT NULL REFERENCES searches(id) ON DELETE CASCADE, combo_idx INTEGER NOT NULL, offer_idx INTEGER NOT NULL, price TEXT NOT NULL, currency TEXT, legs TEXT NOT NULL, fetched_at_ms INTEGER NOT NULL, PRIMARY KEY (search_id, combo_idx, offer_idx));
             CREATE TABLE hidden (search_id INTEGER NOT NULL REFERENCES searches(id) ON DELETE CASCADE, combo_idx INTEGER NOT NULL, reason TEXT NOT NULL, count INTEGER NOT NULL, PRIMARY KEY (search_id, combo_idx, reason));
             PRAGMA user_version = 1;",
        )
        .unwrap();
        let old_request = r#"{"origins":["CGK"],"destinations":["DPS"],"date_from":"2026-12-15","date_through":"2026-12-16","currency":"IDR"}"#;
        conn.execute("INSERT INTO searches (request, created_at_ms, updated_at_ms, stop_reason) VALUES (?1, 1, 2, 'interrupted')", [old_request]).unwrap();
        conn.execute("INSERT INTO combos VALUES (1, 0, 'CGK', 'DPS', '2026-12-15', 'done', NULL, 2), (1, 1, 'CGK', 'DPS', '2026-12-16', 'pending', NULL, NULL)", []).unwrap();
        let legs = serde_json::to_string(&fli_offer("1250000").legs).unwrap();
        conn.execute("INSERT INTO offers VALUES (1, 0, 0, '1250000', 'IDR', ?1, 2)", [legs]).unwrap();
    }
    let store = Store::open(path.to_str().unwrap()).expect("migrates");
    let latest = store.latest().unwrap().unwrap();
    assert_eq!(latest.request.providers, ["fli"]);
    assert_eq!(latest.combos.iter().map(|c| c.provider.as_str()).collect::<Vec<_>>(), ["fli", "fli"]);
    let restored = &latest.offers[0].offer;
    assert_eq!(restored.provider, "fli");
    assert_eq!(restored.price_original, "1250000");
    assert_eq!(restored.price_comparable.as_deref(), Some("1250000"));
    assert_eq!(restored.legs.len(), 1);
    assert_eq!(store.pending(1).unwrap().len(), 1);
    store.finish_combo(1, 1, &[offer("990000")], &[], None, 3).unwrap();
    // Re-opening a migrated file is a no-op.
    drop(store);
    let again = Store::open(path.to_str().unwrap()).expect("reopens");
    assert_eq!(again.latest().unwrap().unwrap().offers.len(), 2);
}
