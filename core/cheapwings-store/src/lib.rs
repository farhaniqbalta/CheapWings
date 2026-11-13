//! On-device search store for the iPad app: one SQLite file holding each search's request,
//! its route/date plan, per-route/date outcome and the exact offers found. One transaction per
//! finished route/date, so a killed app never loses what was already shown.

use cheapwings_core::fli::{FliLeg, FliOffer};
use cheapwings_core::planning::RouteDate;
use rusqlite::{params, Connection, OptionalExtension};
use serde::{Deserialize, Serialize};
use std::fmt;
use std::sync::Mutex;

const SCHEMA_VERSION: i64 = 1;
const KEEP_SEARCHES: i64 = 10;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct StoredRequest {
    pub origins: Vec<String>,
    pub destinations: Vec<String>,
    pub date_from: String,
    pub date_through: String,
    pub currency: String,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ComboStatus {
    Pending,
    Done,
    Failed,
}

impl ComboStatus {
    fn as_str(self) -> &'static str {
        match self {
            Self::Pending => "pending",
            Self::Done => "done",
            Self::Failed => "failed",
        }
    }

    fn parse(text: &str) -> Self {
        match text {
            "done" => Self::Done,
            "failed" => Self::Failed,
            _ => Self::Pending,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct StoredCombo {
    pub index: u32,
    pub route_date: RouteDate,
    pub status: ComboStatus,
    pub code: Option<String>,
    pub finished_at_ms: Option<i64>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct StoredOffer {
    pub combo_index: u32,
    pub offer_index: u32,
    pub offer: FliOffer,
    pub fetched_at_ms: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct StoredSearch {
    pub id: i64,
    pub request: StoredRequest,
    pub created_at_ms: i64,
    pub updated_at_ms: i64,
    /// `finished | cancelled | rate_limited | blocked:<detail> | backgrounded`; None while running.
    pub stop_reason: Option<String>,
    pub combos: Vec<StoredCombo>,
    pub offers: Vec<StoredOffer>,
    /// Hidden-offer reasons summed over the search, sorted by reason.
    pub hidden: Vec<(String, u32)>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum StoreError {
    Open(String),
    Sql(String),
    NotFound(i64),
}

impl StoreError {
    pub fn code(&self) -> &'static str {
        match self {
            Self::Open(_) => "open",
            Self::Sql(_) => "sql",
            Self::NotFound(_) => "not_found",
        }
    }
}

impl fmt::Display for StoreError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Open(why) => write!(f, "could not open the search store: {why}"),
            Self::Sql(why) => write!(f, "search store error: {why}"),
            Self::NotFound(id) => write!(f, "search {id} not found"),
        }
    }
}

impl std::error::Error for StoreError {}

fn sql(err: rusqlite::Error) -> StoreError {
    StoreError::Sql(err.to_string())
}

fn json<T: Serialize>(value: &T) -> Result<String, StoreError> {
    serde_json::to_string(value).map_err(|e| StoreError::Sql(e.to_string()))
}

fn from_json<T: for<'de> Deserialize<'de>>(text: &str) -> Result<T, StoreError> {
    serde_json::from_str(text).map_err(|e| StoreError::Sql(format!("corrupt stored JSON: {e}")))
}

const SCHEMA: &str = "
CREATE TABLE IF NOT EXISTS searches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request TEXT NOT NULL,
    created_at_ms INTEGER NOT NULL,
    updated_at_ms INTEGER NOT NULL,
    stop_reason TEXT
);
CREATE TABLE IF NOT EXISTS combos (
    search_id INTEGER NOT NULL REFERENCES searches(id) ON DELETE CASCADE,
    idx INTEGER NOT NULL,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    date TEXT NOT NULL,
    status TEXT NOT NULL,
    code TEXT,
    finished_at_ms INTEGER,
    PRIMARY KEY (search_id, idx)
);
CREATE TABLE IF NOT EXISTS offers (
    search_id INTEGER NOT NULL REFERENCES searches(id) ON DELETE CASCADE,
    combo_idx INTEGER NOT NULL,
    offer_idx INTEGER NOT NULL,
    price TEXT NOT NULL,
    currency TEXT,
    legs TEXT NOT NULL,
    fetched_at_ms INTEGER NOT NULL,
    PRIMARY KEY (search_id, combo_idx, offer_idx)
);
CREATE TABLE IF NOT EXISTS hidden (
    search_id INTEGER NOT NULL REFERENCES searches(id) ON DELETE CASCADE,
    combo_idx INTEGER NOT NULL,
    reason TEXT NOT NULL,
    count INTEGER NOT NULL,
    PRIMARY KEY (search_id, combo_idx, reason)
);
";

/// Thread-safe handle; every method is one short transaction.
pub struct Store {
    conn: Mutex<Connection>,
}

impl Store {
    pub fn open(path: &str) -> Result<Store, StoreError> {
        let open = |e: rusqlite::Error| StoreError::Open(e.to_string());
        let conn = Connection::open(path).map_err(open)?;
        conn.pragma_update(None, "foreign_keys", true).map_err(open)?;
        conn.query_row("PRAGMA journal_mode = WAL", [], |_| Ok(())).map_err(open)?;
        conn.execute_batch(SCHEMA).map_err(open)?;
        conn.pragma_update(None, "user_version", SCHEMA_VERSION).map_err(open)?;
        Ok(Store { conn: Mutex::new(conn) })
    }

    fn lock(&self) -> std::sync::MutexGuard<'_, Connection> {
        // A panic while holding the lock cannot leave SQLite inconsistent; keep serving.
        self.conn.lock().unwrap_or_else(|poisoned| poisoned.into_inner())
    }

    /// Records a new search with every route/date pending; keeps only the newest 10 searches.
    pub fn create_search(&self, request: &StoredRequest, combos: &[RouteDate], now_ms: i64) -> Result<i64, StoreError> {
        let mut conn = self.lock();
        let tx = conn.transaction().map_err(sql)?;
        tx.execute(
            "INSERT INTO searches (request, created_at_ms, updated_at_ms) VALUES (?1, ?2, ?2)",
            params![json(request)?, now_ms],
        )
        .map_err(sql)?;
        let id = tx.last_insert_rowid();
        {
            let mut insert = tx
                .prepare("INSERT INTO combos (search_id, idx, origin, destination, date, status) VALUES (?1, ?2, ?3, ?4, ?5, 'pending')")
                .map_err(sql)?;
            for (index, combo) in combos.iter().enumerate() {
                insert.execute(params![id, index as i64, combo.origin, combo.destination, combo.date]).map_err(sql)?;
            }
        }
        tx.execute(
            "DELETE FROM searches WHERE id NOT IN (SELECT id FROM searches ORDER BY id DESC LIMIT ?1)",
            params![KEEP_SEARCHES],
        )
        .map_err(sql)?;
        tx.commit().map_err(sql)?;
        Ok(id)
    }

    /// One transaction per finished route/date. Re-finishing replaces that route/date's data.
    pub fn finish_combo(
        &self,
        search_id: i64,
        index: u32,
        offers: &[FliOffer],
        hidden: &[String],
        failure: Option<&str>,
        now_ms: i64,
    ) -> Result<(), StoreError> {
        let mut conn = self.lock();
        let tx = conn.transaction().map_err(sql)?;
        let status = if failure.is_some() { ComboStatus::Failed } else { ComboStatus::Done };
        let updated = tx
            .execute(
                "UPDATE combos SET status = ?3, code = ?4, finished_at_ms = ?5 WHERE search_id = ?1 AND idx = ?2",
                params![search_id, index, status.as_str(), failure, now_ms],
            )
            .map_err(sql)?;
        if updated == 0 {
            return Err(StoreError::NotFound(search_id));
        }
        tx.execute("DELETE FROM offers WHERE search_id = ?1 AND combo_idx = ?2", params![search_id, index]).map_err(sql)?;
        tx.execute("DELETE FROM hidden WHERE search_id = ?1 AND combo_idx = ?2", params![search_id, index]).map_err(sql)?;
        {
            let mut insert = tx
                .prepare("INSERT INTO offers (search_id, combo_idx, offer_idx, price, currency, legs, fetched_at_ms) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)")
                .map_err(sql)?;
            for (offer_index, offer) in offers.iter().enumerate() {
                insert
                    .execute(params![search_id, index, offer_index as i64, offer.price, offer.currency, json(&offer.legs)?, now_ms])
                    .map_err(sql)?;
            }
            let mut counts: Vec<(&String, u32)> = Vec::new();
            for reason in hidden {
                match counts.iter_mut().find(|(r, _)| *r == reason) {
                    Some((_, n)) => *n += 1,
                    None => counts.push((reason, 1)),
                }
            }
            let mut insert_hidden = tx
                .prepare("INSERT INTO hidden (search_id, combo_idx, reason, count) VALUES (?1, ?2, ?3, ?4)")
                .map_err(sql)?;
            for (reason, count) in counts {
                insert_hidden.execute(params![search_id, index, reason, count]).map_err(sql)?;
            }
        }
        tx.execute("UPDATE searches SET updated_at_ms = ?2 WHERE id = ?1", params![search_id, now_ms]).map_err(sql)?;
        tx.commit().map_err(sql)
    }

    pub fn set_stopped(&self, search_id: i64, reason: &str, now_ms: i64) -> Result<(), StoreError> {
        let n = self
            .lock()
            .execute(
                "UPDATE searches SET stop_reason = ?2, updated_at_ms = ?3 WHERE id = ?1",
                params![search_id, reason, now_ms],
            )
            .map_err(sql)?;
        if n == 0 { Err(StoreError::NotFound(search_id)) } else { Ok(()) }
    }

    /// Called when a stopped search is resumed.
    pub fn clear_stopped(&self, search_id: i64) -> Result<(), StoreError> {
        let n = self.lock().execute("UPDATE searches SET stop_reason = NULL WHERE id = ?1", params![search_id]).map_err(sql)?;
        if n == 0 { Err(StoreError::NotFound(search_id)) } else { Ok(()) }
    }

    pub fn search_count(&self) -> Result<i64, StoreError> {
        self.lock().query_row("SELECT COUNT(*) FROM searches", [], |r| r.get(0)).map_err(sql)
    }

    pub fn pending(&self, search_id: i64) -> Result<Vec<StoredCombo>, StoreError> {
        let conn = self.lock();
        Self::require(&conn, search_id)?;
        Ok(Self::combos(&conn, search_id)?.into_iter().filter(|c| c.status == ComboStatus::Pending).collect())
    }

    pub fn latest(&self) -> Result<Option<StoredSearch>, StoreError> {
        let conn = self.lock();
        let row = conn
            .query_row(
                "SELECT id, request, created_at_ms, updated_at_ms, stop_reason FROM searches ORDER BY id DESC LIMIT 1",
                [],
                |r| Ok((r.get::<_, i64>(0)?, r.get::<_, String>(1)?, r.get(2)?, r.get(3)?, r.get(4)?)),
            )
            .optional()
            .map_err(sql)?;
        let Some((id, request, created_at_ms, updated_at_ms, stop_reason)) = row else { return Ok(None) };
        Ok(Some(StoredSearch {
            id,
            request: from_json(&request)?,
            created_at_ms,
            updated_at_ms,
            stop_reason,
            combos: Self::combos(&conn, id)?,
            offers: Self::offers(&conn, id)?,
            hidden: Self::hidden(&conn, id)?,
        }))
    }

    fn require(conn: &Connection, search_id: i64) -> Result<(), StoreError> {
        let found: Option<i64> = conn
            .query_row("SELECT id FROM searches WHERE id = ?1", params![search_id], |r| r.get(0))
            .optional()
            .map_err(sql)?;
        found.map(|_| ()).ok_or(StoreError::NotFound(search_id))
    }

    fn combos(conn: &Connection, search_id: i64) -> Result<Vec<StoredCombo>, StoreError> {
        let mut stmt = conn
            .prepare("SELECT idx, origin, destination, date, status, code, finished_at_ms FROM combos WHERE search_id = ?1 ORDER BY idx")
            .map_err(sql)?;
        let rows = stmt
            .query_map(params![search_id], |r| {
                Ok(StoredCombo {
                    index: r.get(0)?,
                    route_date: RouteDate { origin: r.get(1)?, destination: r.get(2)?, date: r.get(3)? },
                    status: ComboStatus::parse(&r.get::<_, String>(4)?),
                    code: r.get(5)?,
                    finished_at_ms: r.get(6)?,
                })
            })
            .map_err(sql)?;
        rows.collect::<Result<Vec<_>, _>>().map_err(sql)
    }

    fn offers(conn: &Connection, search_id: i64) -> Result<Vec<StoredOffer>, StoreError> {
        let mut stmt = conn
            .prepare("SELECT combo_idx, offer_idx, price, currency, legs, fetched_at_ms FROM offers WHERE search_id = ?1 ORDER BY combo_idx, offer_idx")
            .map_err(sql)?;
        let rows = stmt
            .query_map(params![search_id], |r| {
                Ok((r.get::<_, u32>(0)?, r.get::<_, u32>(1)?, r.get::<_, String>(2)?, r.get::<_, Option<String>>(3)?, r.get::<_, String>(4)?, r.get::<_, i64>(5)?))
            })
            .map_err(sql)?;
        let mut out = Vec::new();
        for row in rows {
            let (combo_index, offer_index, price, currency, legs, fetched_at_ms) = row.map_err(sql)?;
            let legs: Vec<FliLeg> = from_json(&legs)?;
            out.push(StoredOffer { combo_index, offer_index, offer: FliOffer { price, currency, legs }, fetched_at_ms });
        }
        Ok(out)
    }

    fn hidden(conn: &Connection, search_id: i64) -> Result<Vec<(String, u32)>, StoreError> {
        let mut stmt = conn
            .prepare("SELECT reason, SUM(count) FROM hidden WHERE search_id = ?1 GROUP BY reason ORDER BY reason")
            .map_err(sql)?;
        let rows = stmt.query_map(params![search_id], |r| Ok((r.get(0)?, r.get(1)?))).map_err(sql)?;
        rows.collect::<Result<Vec<_>, _>>().map_err(sql)
    }
}
