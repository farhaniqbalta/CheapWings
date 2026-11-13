//! UniFFI surface of `cheapwings-core` for Swift. Thin wrappers only: records mirror the core
//! types and every function delegates. UniFFI has no i128, so minor units cross as text.

use cheapwings_core::{fingerprint as fp, fli, locations, money, planning, ranking};

uniffi::setup_scaffolding!();

#[derive(Debug, thiserror::Error, uniffi::Error)]
pub enum CoreError {
    #[error("{message}")]
    Invalid { message: String },
}

impl From<money::MoneyError> for CoreError {
    fn from(err: money::MoneyError) -> Self {
        Self::Invalid { message: err.to_string() }
    }
}

#[derive(Debug, thiserror::Error, uniffi::Error)]
pub enum FliDecodeError {
    /// `code` is the backend `ProviderFailure` code (`schema_changed`, `partial_payload`, `auth_denied`).
    #[error("{code}: {detail}")]
    Failed { code: String, detail: String },
}

#[derive(Debug, thiserror::Error, uniffi::Error)]
pub enum PlanSearchError {
    /// `code`: `invalid_airport | no_airports | dates_reversed | invalid_date | same_airport | too_many`.
    #[error("{code}: {detail}")]
    Rejected { code: String, detail: String },
}

// ---------- planning ----------

#[derive(Debug, Clone, PartialEq, Eq, uniffi::Record)]
pub struct RouteDate {
    pub origin: String,
    pub destination: String,
    pub date: String,
}

#[uniffi::export]
pub fn plan_search(
    origins: Vec<String>,
    destinations: Vec<String>,
    date_from: String,
    date_through: String,
    max_combinations: u32,
) -> Result<Vec<RouteDate>, PlanSearchError> {
    planning::plan_search(&origins, &destinations, &date_from, &date_through, max_combinations)
        .map(|combos| {
            combos
                .into_iter()
                .map(|c| RouteDate { origin: c.origin, destination: c.destination, date: c.date })
                .collect()
        })
        .map_err(|e| PlanSearchError::Rejected { code: e.code().to_owned(), detail: e.to_string() })
}

// ---------- money ----------

#[uniffi::export]
pub fn minor_unit_exponent(currency: String) -> Result<u32, CoreError> {
    Ok(money::minor_unit_exponent(&currency)?)
}

#[uniffi::export]
pub fn from_minor_units(minor: String, currency: String) -> Result<String, CoreError> {
    let minor: i128 = minor.parse().map_err(|_| CoreError::Invalid { message: format!("invalid minor units {minor:?}") })?;
    Ok(money::from_minor_units(minor, &currency)?)
}

#[uniffi::export]
pub fn as_minor_units(amount: String, currency: String) -> Result<String, CoreError> {
    Ok(money::as_minor_units(&amount, &currency)?.to_string())
}

#[uniffi::export]
pub fn fx_convert(amount: String, rate: String, quote_currency: String) -> Result<String, CoreError> {
    Ok(money::fx_convert(&amount, &rate, &quote_currency)?)
}

// ---------- fingerprint ----------

#[derive(uniffi::Record)]
pub struct LocalInstant {
    pub y: i32,
    pub mo: u32,
    pub d: u32,
    pub h: u32,
    pub mi: u32,
    pub s: u32,
    pub us: u32,
    pub offset: i32,
}

#[derive(uniffi::Record)]
pub struct Segment {
    pub ordinal: u32,
    pub marketing: String,
    pub operating: String,
    pub flight: String,
    pub origin: String,
    pub destination: String,
    pub depart: LocalInstant,
    pub arrive: LocalInstant,
}

impl From<LocalInstant> for fp::LocalInstant {
    fn from(t: LocalInstant) -> Self {
        Self { y: t.y, mo: t.mo, d: t.d, h: t.h, mi: t.mi, s: t.s, us: t.us, offset: t.offset }
    }
}

#[uniffi::export]
pub fn fingerprint(segments: Vec<Segment>) -> String {
    let segments: Vec<fp::Segment> = segments
        .into_iter()
        .map(|s| fp::Segment {
            ordinal: s.ordinal,
            marketing: s.marketing,
            operating: s.operating,
            flight: s.flight,
            origin: s.origin,
            destination: s.destination,
            depart: s.depart.into(),
            arrive: s.arrive.into(),
        })
        .collect();
    fp::fingerprint(&segments)
}

// ---------- ranking ----------

#[derive(uniffi::Record)]
pub struct RankOffer {
    pub id: String,
    pub price_status: String,
    pub hidden_city: String,
    pub comparison_status: String,
    pub amount: Option<String>,
}

fn rank_groups(groups: Vec<Vec<RankOffer>>) -> Vec<Vec<ranking::RankOffer>> {
    groups
        .into_iter()
        .map(|g| {
            g.into_iter()
                .map(|o| ranking::RankOffer {
                    id: o.id,
                    price_status: o.price_status,
                    hidden_city: o.hidden_city,
                    comparison_status: o.comparison_status,
                    amount: o.amount,
                })
                .collect()
        })
        .collect()
}

#[uniffi::export]
pub fn best_checked_deal(groups: Vec<Vec<RankOffer>>) -> Vec<String> {
    ranking::best_checked_deal(&rank_groups(groups))
}

#[uniffi::export]
pub fn lowest_advertised(groups: Vec<Vec<RankOffer>>) -> Vec<String> {
    ranking::lowest_advertised(&rank_groups(groups))
}

// ---------- Fli ----------

#[derive(Debug, PartialEq, Eq, uniffi::Record)]
pub struct FliLeg {
    pub origin: String,
    pub destination: String,
    pub airline: String,
    pub flight_number: String,
    pub depart_local: String,
    pub arrive_local: String,
}

#[derive(Debug, PartialEq, Eq, uniffi::Record)]
pub struct FliOffer {
    pub price: String,
    pub currency: Option<String>,
    pub legs: Vec<FliLeg>,
}

#[derive(Debug, PartialEq, Eq, uniffi::Record)]
pub struct FliPage {
    pub offers: Vec<FliOffer>,
    pub unpriced: u32,
}

impl From<fli::FliPage> for FliPage {
    fn from(page: fli::FliPage) -> Self {
        let offers = page
            .offers
            .into_iter()
            .map(|o| FliOffer {
                price: o.price,
                currency: o.currency,
                legs: o
                    .legs
                    .into_iter()
                    .map(|l| FliLeg {
                        origin: l.origin,
                        destination: l.destination,
                        airline: l.airline,
                        flight_number: l.flight_number,
                        depart_local: l.depart_local,
                        arrive_local: l.arrive_local,
                    })
                    .collect(),
            })
            .collect();
        Self { offers, unpriced: page.unpriced }
    }
}

impl From<FliPage> for fli::FliPage {
    fn from(page: FliPage) -> Self {
        let offers = page
            .offers
            .into_iter()
            .map(|o| fli::FliOffer {
                price: o.price,
                currency: o.currency,
                legs: o
                    .legs
                    .into_iter()
                    .map(|l| fli::FliLeg {
                        origin: l.origin,
                        destination: l.destination,
                        airline: l.airline,
                        flight_number: l.flight_number,
                        depart_local: l.depart_local,
                        arrive_local: l.arrive_local,
                    })
                    .collect(),
            })
            .collect();
        Self { offers, unpriced: page.unpriced }
    }
}

#[uniffi::export]
pub fn fli_search_url(origin: String, destination: String, date: String, currency: String, country: String) -> String {
    fli::search_url(&origin, &destination, &date, &currency, &country)
}

#[uniffi::export]
pub fn fli_decode_page(html: String) -> Result<FliPage, FliDecodeError> {
    fli::decode_page(&html)
        .map(FliPage::from)
        .map_err(|e| FliDecodeError::Failed { code: e.code().to_owned(), detail: e.to_string() })
}

#[derive(Debug, PartialEq, Eq, uniffi::Record)]
pub struct FliCheckedOffers {
    pub offers: Vec<FliOffer>,
    /// One reason per dropped offer (e.g. `currency None`).
    pub rejected: Vec<String>,
}

#[uniffi::export]
pub fn fli_filter_offers(
    page: FliPage,
    origin: String,
    destination: String,
    date: String,
    currency: String,
    max_stops: Option<u32>,
) -> FliCheckedOffers {
    let checked = fli::filter_offers(&page.into(), &origin, &destination, &date, &currency, max_stops);
    let offers = FliPage::from(fli::FliPage { offers: checked.offers, unpriced: 0 }).offers;
    FliCheckedOffers { offers, rejected: checked.rejected }
}

#[derive(Debug, Clone, PartialEq, Eq, uniffi::Record)]
pub struct AirportChange {
    pub from: String,
    pub to: String,
}

#[uniffi::export]
pub fn fli_airport_changes(offer: FliOffer) -> Vec<AirportChange> {
    let page = fli::FliPage::from(FliPage { offers: vec![offer], unpriced: 0 });
    fli::airport_changes(&page.offers[0]).into_iter().map(|(from, to)| AirportChange { from, to }).collect()
}

// ---------- location catalog ----------

#[derive(Debug, thiserror::Error, uniffi::Error)]
pub enum CatalogError {
    /// `code`: `invalid | too_long | unknown_location | stale_version | type_mismatch | no_major_mapping`.
    #[error("{code}: {message}")]
    Failed { code: String, message: String },
}

impl From<locations::CatalogError> for CatalogError {
    fn from(err: locations::CatalogError) -> Self {
        Self::Failed { code: err.code().to_owned(), message: err.to_string() }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, uniffi::Record)]
pub struct Location {
    pub id: String,
    /// `airport | city | country`
    pub kind: String,
    pub name: String,
    pub code: Option<String>,
    pub city: Option<String>,
    pub country: String,
    pub country_name: String,
    pub codes: Vec<String>,
    pub timezone: Option<String>,
}

impl From<locations::Location> for Location {
    fn from(l: locations::Location) -> Self {
        Self {
            id: l.id,
            kind: l.kind,
            name: l.name,
            code: l.code,
            city: l.city,
            country: l.country,
            country_name: l.country_name,
            codes: l.codes,
            timezone: l.timezone,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, uniffi::Record)]
pub struct MajorResolution {
    pub codes: Vec<String>,
    pub rationale: String,
    pub definition: String,
}

/// The shared airport/city/country catalog (same JSON as the backend and web app).
#[derive(uniffi::Object)]
pub struct LocationCatalog {
    inner: locations::Catalog,
}

#[uniffi::export]
impl LocationCatalog {
    #[uniffi::constructor]
    pub fn new(json: String) -> Result<std::sync::Arc<Self>, CatalogError> {
        Ok(std::sync::Arc::new(Self { inner: locations::Catalog::from_json(&json)? }))
    }

    pub fn version(&self) -> String {
        self.inner.version().to_owned()
    }

    pub fn search(&self, text: String, within: Option<String>) -> Result<Vec<Location>, CatalogError> {
        Ok(self.inner.search(&text, within.as_deref())?.into_iter().map(Location::from).collect())
    }

    pub fn airports_of(&self, id: String) -> Result<Vec<Location>, CatalogError> {
        Ok(self.inner.airports_of(&id)?.into_iter().map(Location::from).collect())
    }

    pub fn has_major(&self, id: String) -> bool {
        self.inner.has_major(&id)
    }

    pub fn resolve_major(&self, kind: String, id: String, version: String) -> Result<MajorResolution, CatalogError> {
        let r = self.inner.resolve_major(&kind, &id, &version)?;
        Ok(MajorResolution { codes: r.codes, rationale: r.rationale, definition: r.definition })
    }

    pub fn location(&self, id: String) -> Option<Location> {
        self.inner.location(&id).map(Location::from)
    }

    pub fn airport(&self, code: String) -> Option<Location> {
        self.inner.airport(&code).map(Location::from)
    }
}

#[uniffi::export]
pub fn fli_cross_check(page: FliPage, origin: String, destination: String, date: String, currency: String) -> Option<String> {
    fli::cross_check(&page.into(), &origin, &destination, &date, &currency)
}

// ---------- on-device search store ----------

use cheapwings_store as store;
use std::sync::Arc;

#[derive(Debug, thiserror::Error, uniffi::Error)]
pub enum StoreError {
    /// `code`: `open | sql | not_found`.
    #[error("{code}: {message}")]
    Failed { code: String, message: String },
}

impl From<store::StoreError> for StoreError {
    fn from(err: store::StoreError) -> Self {
        Self::Failed { code: err.code().to_owned(), message: err.to_string() }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, uniffi::Record)]
pub struct StoredRequest {
    pub origins: Vec<String>,
    pub destinations: Vec<String>,
    pub date_from: String,
    pub date_through: String,
    pub currency: String,
    #[uniffi(default = None)]
    pub max_stops: Option<u32>,
    #[uniffi(default = None)]
    pub origin_major: Option<String>,
    #[uniffi(default = None)]
    pub destination_major: Option<String>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, uniffi::Enum)]
pub enum ComboStatus {
    Pending,
    Done,
    Failed,
}

#[derive(Debug, Clone, PartialEq, Eq, uniffi::Record)]
pub struct StoredCombo {
    pub index: u32,
    pub route_date: RouteDate,
    pub status: ComboStatus,
    pub code: Option<String>,
    pub finished_at_ms: Option<i64>,
}

#[derive(Debug, PartialEq, Eq, uniffi::Record)]
pub struct StoredOffer {
    pub combo_index: u32,
    pub offer_index: u32,
    pub offer: FliOffer,
    pub fetched_at_ms: i64,
}

#[derive(Debug, Clone, PartialEq, Eq, uniffi::Record)]
pub struct HiddenCount {
    pub reason: String,
    pub count: u32,
}

#[derive(Debug, PartialEq, Eq, uniffi::Record)]
pub struct StoredSearch {
    pub id: i64,
    pub request: StoredRequest,
    pub created_at_ms: i64,
    pub updated_at_ms: i64,
    pub stop_reason: Option<String>,
    pub combos: Vec<StoredCombo>,
    pub offers: Vec<StoredOffer>,
    pub hidden: Vec<HiddenCount>,
}

fn route_to_core(c: RouteDate) -> planning::RouteDate {
    planning::RouteDate { origin: c.origin, destination: c.destination, date: c.date }
}

fn route_from_core(c: planning::RouteDate) -> RouteDate {
    RouteDate { origin: c.origin, destination: c.destination, date: c.date }
}

fn combo_from_store(c: store::StoredCombo) -> StoredCombo {
    StoredCombo {
        index: c.index,
        route_date: route_from_core(c.route_date),
        status: match c.status {
            store::ComboStatus::Pending => ComboStatus::Pending,
            store::ComboStatus::Done => ComboStatus::Done,
            store::ComboStatus::Failed => ComboStatus::Failed,
        },
        code: c.code,
        finished_at_ms: c.finished_at_ms,
    }
}

/// The app's on-device history: one SQLite file, one transaction per finished route/date.
#[derive(uniffi::Object)]
pub struct SearchStore {
    inner: store::Store,
}

#[uniffi::export]
impl SearchStore {
    #[uniffi::constructor]
    pub fn new(path: String) -> Result<Arc<Self>, StoreError> {
        Ok(Arc::new(Self { inner: store::Store::open(&path)? }))
    }

    pub fn create_search(&self, request: StoredRequest, combos: Vec<RouteDate>, now_ms: i64) -> Result<i64, StoreError> {
        let request = store::StoredRequest {
            origins: request.origins,
            destinations: request.destinations,
            date_from: request.date_from,
            date_through: request.date_through,
            currency: request.currency,
            max_stops: request.max_stops,
            origin_major: request.origin_major,
            destination_major: request.destination_major,
        };
        let combos: Vec<planning::RouteDate> = combos.into_iter().map(route_to_core).collect();
        Ok(self.inner.create_search(&request, &combos, now_ms)?)
    }

    pub fn finish_combo(
        &self,
        search_id: i64,
        index: u32,
        offers: Vec<FliOffer>,
        hidden: Vec<String>,
        failure: Option<String>,
        now_ms: i64,
    ) -> Result<(), StoreError> {
        let offers = fli::FliPage::from(FliPage { offers, unpriced: 0 }).offers;
        Ok(self.inner.finish_combo(search_id, index, &offers, &hidden, failure.as_deref(), now_ms)?)
    }

    pub fn set_stopped(&self, search_id: i64, reason: String, now_ms: i64) -> Result<(), StoreError> {
        Ok(self.inner.set_stopped(search_id, &reason, now_ms)?)
    }

    pub fn clear_stopped(&self, search_id: i64) -> Result<(), StoreError> {
        Ok(self.inner.clear_stopped(search_id)?)
    }

    pub fn pending(&self, search_id: i64) -> Result<Vec<StoredCombo>, StoreError> {
        Ok(self.inner.pending(search_id)?.into_iter().map(combo_from_store).collect())
    }

    pub fn latest(&self) -> Result<Option<StoredSearch>, StoreError> {
        let Some(s) = self.inner.latest()? else { return Ok(None) };
        let offer_page = FliPage::from(fli::FliPage { offers: s.offers.iter().map(|o| o.offer.clone()).collect(), unpriced: 0 });
        let offers = s
            .offers
            .iter()
            .zip(offer_page.offers)
            .map(|(stored, offer)| StoredOffer {
                combo_index: stored.combo_index,
                offer_index: stored.offer_index,
                offer,
                fetched_at_ms: stored.fetched_at_ms,
            })
            .collect();
        Ok(Some(StoredSearch {
            id: s.id,
            request: StoredRequest {
                origins: s.request.origins,
                destinations: s.request.destinations,
                date_from: s.request.date_from,
                date_through: s.request.date_through,
                currency: s.request.currency,
                max_stops: s.request.max_stops,
                origin_major: s.request.origin_major,
                destination_major: s.request.destination_major,
            },
            created_at_ms: s.created_at_ms,
            updated_at_ms: s.updated_at_ms,
            stop_reason: s.stop_reason,
            combos: s.combos.into_iter().map(combo_from_store).collect(),
            offers,
            hidden: s.hidden.into_iter().map(|(reason, count)| HiddenCount { reason, count }).collect(),
        }))
    }
}
