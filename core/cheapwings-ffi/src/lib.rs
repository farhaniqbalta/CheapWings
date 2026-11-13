//! UniFFI surface of `cheapwings-core` for Swift. Thin wrappers only: records mirror the core
//! types and every function delegates. UniFFI has no i128, so minor units cross as text.

use cheapwings_core::{fingerprint as fp, fli, money, planning, ranking};

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

#[uniffi::export]
pub fn fli_cross_check(page: FliPage, origin: String, destination: String, date: String, currency: String) -> Option<String> {
    fli::cross_check(&page.into(), &origin, &destination, &date, &currency)
}
