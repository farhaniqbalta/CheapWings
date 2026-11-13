use cheapwings_core::fli::{FliLeg, FliOffer};
use cheapwings_core::planning::RouteDate;
use cheapwings_store::{ComboStatus, Store, StoreError, StoredRequest};

fn request() -> StoredRequest {
    StoredRequest {
        origins: vec!["CGK".into()],
        destinations: vec!["DPS".into()],
        date_from: "2026-12-15".into(),
        date_through: "2026-12-17".into(),
        currency: "IDR".into(),
    }
}

fn combos() -> Vec<RouteDate> {
    ["2026-12-15", "2026-12-16", "2026-12-17"]
        .iter()
        .map(|d| RouteDate { origin: "CGK".into(), destination: "DPS".into(), date: (*d).into() })
        .collect()
}

fn offer(price: &str) -> FliOffer {
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
    assert_eq!(latest.offers.iter().map(|o| o.offer.price.as_str()).collect::<Vec<_>>(), ["3"]);
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
    assert_eq!(latest.offers[0].offer.price, "1250000");
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
