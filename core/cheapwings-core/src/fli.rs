//! Google Flights (Fli) search URL and `ds:1` page decoder.
//!
//! Ports fli 881aee5 (MIT, Punit Arani) `_proto` tfs encoding, `_tfs` ds:1 extraction and
//! `_decoders` row layout, with CheapWings' rules from `providers/fli.py`. No networking:
//! callers fetch the page and pass its text in.

use base64::engine::general_purpose::URL_SAFE_NO_PAD;
use base64::Engine;
use regex::Regex;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::fmt;
use std::sync::OnceLock;

// ---------- search URL ----------

fn varint(mut value: u64) -> Vec<u8> {
    let mut out = Vec::new();
    loop {
        let byte = (value & 0x7F) as u8;
        value >>= 7;
        if value == 0 {
            out.push(byte);
            return out;
        }
        out.push(byte | 0x80);
    }
}

fn varint_field(field: u64, value: u64) -> Vec<u8> {
    [varint(field << 3), varint(value)].concat()
}

fn length_delimited(field: u64, bytes: &[u8]) -> Vec<u8> {
    [varint(field << 3 | 2), varint(bytes.len() as u64), bytes.to_vec()].concat()
}

/// `tfs` for CheapWings' only query: one-way, one adult, economy, any stops.
pub fn tfs(origin: &str, destination: &str, date: &str) -> String {
    let airport = |field, code: &str| {
        length_delimited(field, &[varint_field(1, 1), length_delimited(2, code.as_bytes())].concat())
    };
    // Field order matters for byte equality with fli: date, origin (13), destination (14).
    let segment = [length_delimited(2, date.as_bytes()), airport(13, origin), airport(14, destination)].concat();
    let payload = [
        varint_field(1, 28),
        varint_field(2, 2),
        length_delimited(3, &segment),
        varint_field(8, 1),  // one adult
        varint_field(9, 1),  // economy
        varint_field(14, 1),
        varint_field(19, 2), // one-way
    ]
    .concat();
    URL_SAFE_NO_PAD.encode(payload)
}

pub fn search_url(origin: &str, destination: &str, date: &str, currency: &str, country: &str) -> String {
    format!(
        "https://www.google.com/travel/flights?tfs={}&hl=en&gl={country}&curr={currency}",
        tfs(origin, destination, date)
    )
}

// ---------- page decoding ----------

#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize)]
pub struct FliLeg {
    pub origin: String,
    pub destination: String,
    pub airline: String,
    pub flight_number: String,
    /// Naive local wall time `YYYY-MM-DDTHH:MM`, as Google sends it.
    pub depart_local: String,
    pub arrive_local: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize)]
pub struct FliOffer {
    /// Exact price text from the page (e.g. `"1234.50"`); never a float.
    pub price: String,
    pub currency: Option<String>,
    pub legs: Vec<FliLeg>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FliPage {
    pub offers: Vec<FliOffer>,
    pub unpriced: u32,
}

/// Failure codes match `ProviderFailure` in the Python backend.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum FliError {
    SchemaChanged(String),
    PartialPayload,
    AuthDenied,
}

impl FliError {
    pub fn code(&self) -> &'static str {
        match self {
            Self::SchemaChanged(_) => "schema_changed",
            Self::PartialPayload => "partial_payload",
            Self::AuthDenied => "auth_denied",
        }
    }
}

impl fmt::Display for FliError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::SchemaChanged(why) => write!(f, "schema_changed: {why}"),
            other => f.write_str(other.code()),
        }
    }
}

impl std::error::Error for FliError {}

const MAX_ROWS: usize = 500;

fn schema(why: &str) -> FliError {
    FliError::SchemaChanged(why.to_owned())
}

struct Patterns {
    blob: Regex,
    key: Regex,
    data: Regex,
}

fn patterns() -> &'static Patterns {
    static PATTERNS: OnceLock<Patterns> = OnceLock::new();
    PATTERNS.get_or_init(|| Patterns {
        blob: Regex::new(r"(?s)AF_initDataCallback\((\{.*?\})\);").expect("valid regex"),
        key: Regex::new(r"key:\s*'([^']+)'").expect("valid regex"),
        data: Regex::new(r"(?s)data:(.*?), sideChannel").expect("valid regex"),
    })
}

/// The parsed `ds:1` payload, or None when the page has none (or it is not valid JSON).
fn extract_ds1(html: &str) -> Option<Value> {
    let p = patterns();
    p.blob.captures_iter(html).find_map(|blob| {
        let body = blob.get(1)?.as_str();
        if p.key.captures(body)?.get(1)?.as_str() != "ds:1" {
            return None;
        }
        serde_json::from_str(p.data.captures(body)?.get(1)?.as_str()).ok()
    })
}

/// Decodes a Google Flights search page into priced offers.
pub fn decode_page(html: &str) -> Result<FliPage, FliError> {
    let lower = html.to_lowercase();
    if lower.contains("our systems have detected unusual traffic") || lower.contains("unusual traffic from your computer") {
        return Err(FliError::AuthDenied);
    }
    let payload = extract_ds1(html).ok_or_else(|| schema("no ds:1 payload"))?;
    let data = payload.as_array().filter(|d| d.len() >= 4).ok_or_else(|| schema("payload shape"))?;

    let mut rows: Vec<&Value> = Vec::new();
    let mut saw_group = false;
    for group in &data[2..4] {
        match group {
            Value::Null => continue,
            Value::Array(g) => {
                let first = g.first().and_then(Value::as_array).ok_or_else(|| schema("row group"))?;
                saw_group = true;
                rows.extend(first);
            }
            _ => return Err(schema("row group")),
        }
    }
    if rows.len() > MAX_ROWS {
        return Err(FliError::PartialPayload);
    }
    if !saw_group {
        return Err(schema("no row groups"));
    }

    let mut offers = Vec::new();
    let mut unpriced = 0;
    for row in rows {
        let row = row.as_array().ok_or_else(|| schema("row"))?;
        let price_block = row.get(1).and_then(Value::as_array).ok_or_else(|| schema("price block"))?;
        let head = price_block.first().and_then(Value::as_array).ok_or_else(|| schema("price head"))?;
        if head.is_empty() {
            unpriced += 1;
            continue;
        }
        let price = match head.last() {
            Some(Value::Number(n)) => n.to_string(),
            _ => return Err(schema("price")),
        };
        let currency = price_block.get(1).and_then(Value::as_str).and_then(currency_from_token);
        let detail = row.first().and_then(Value::as_array).ok_or_else(|| schema("detail"))?;
        let legs = match detail.get(2) {
            Some(Value::Array(legs)) => legs.iter().map(leg).collect::<Result<Vec<_>, _>>()?,
            Some(Value::Null) => Vec::new(),
            _ => return Err(schema("legs")),
        };
        offers.push(FliOffer { price, currency, legs });
    }
    Ok(FliPage { offers, unpriced })
}

fn text(value: Option<&Value>) -> Option<String> {
    match value? {
        Value::String(s) => Some(s.clone()),
        Value::Number(n) => Some(n.to_string()),
        _ => None,
    }
}

fn leg(value: &Value) -> Result<FliLeg, FliError> {
    let fl = value.as_array().filter(|fl| fl.len() > 22).ok_or_else(|| schema("leg shape"))?;
    let airline = fl[22].as_array();
    Ok(FliLeg {
        origin: fl[3].as_str().ok_or_else(|| schema("leg origin"))?.to_owned(),
        destination: fl[6].as_str().ok_or_else(|| schema("leg destination"))?.to_owned(),
        airline: airline.and_then(|a| text(a.first())).unwrap_or_default(),
        flight_number: airline.and_then(|a| text(a.get(1))).unwrap_or_default(),
        depart_local: local_time(&fl[20], &fl[8])?,
        arrive_local: local_time(&fl[21], &fl[10])?,
    })
}

/// `[y, m, d]` + `[h, m]` with nulls as 0 (fli `_parse_datetime`).
fn local_time(date: &Value, time: &Value) -> Result<String, FliError> {
    let parts = |v: &Value, n: usize| {
        let mut out: Vec<u64> = v.as_array().map(|a| a.iter().map(|x| x.as_u64().unwrap_or(0)).collect()).unwrap_or_default();
        out.resize(n.max(out.len()), 0);
        out
    };
    let (d, t) = (parts(date, 3), parts(time, 2));
    if d[0] == 0 {
        return Err(schema("leg date"));
    }
    Ok(format!("{:04}-{:02}-{:02}T{:02}:{:02}", d[0], d[1], d[2], t[0], t[1]))
}

/// fli `core/currency.py`: base64url protobuf, field 3 → nested field 3 = ISO code.
fn currency_from_token(token: &str) -> Option<String> {
    let bytes = URL_SAFE_NO_PAD.decode(token.trim_end_matches('=')).ok()?;
    let nested = length_field(3, &bytes)?;
    Some(String::from_utf8(length_field(3, nested)?.to_vec()).ok()?.to_uppercase())
}

/// First length-delimited field `number`, skipping other fields. None on malformed input.
fn length_field(number: u64, bytes: &[u8]) -> Option<&[u8]> {
    let mut i = 0;
    let read_varint = |i: &mut usize| -> Option<u64> {
        let mut result = 0u64;
        for shift in (0..64).step_by(7) {
            let b = *bytes.get(*i)?;
            *i += 1;
            result |= u64::from(b & 0x7F) << shift;
            if b & 0x80 == 0 {
                return Some(result);
            }
        }
        None
    };
    while i < bytes.len() {
        let tag = read_varint(&mut i)?;
        match tag & 7 {
            0 => {
                read_varint(&mut i)?;
            }
            1 => i += 8,
            5 => i += 4,
            2 => {
                let len = usize::try_from(read_varint(&mut i)?).ok()?;
                let end = i.checked_add(len).filter(|end| *end <= bytes.len())?;
                if tag >> 3 == number {
                    return Some(&bytes[i..end]);
                }
                i = end;
            }
            _ => return None,
        }
    }
    None
}

/// None when every priced offer matches the query; otherwise the first mismatch.
pub fn cross_check(page: &FliPage, origin: &str, destination: &str, date: &str, currency: &str) -> Option<String> {
    page.offers.iter().find_map(|o| offer_mismatch(o, origin, destination, date, currency))
}

/// Offers that match the query, and one reason per offer that does not.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CheckedOffers {
    pub offers: Vec<FliOffer>,
    pub rejected: Vec<String>,
}

/// Per-offer version of `cross_check`: one bad row (e.g. a row Google sends without a
/// currency token) no longer discards every other offer on the page.
pub fn filter_offers(page: &FliPage, origin: &str, destination: &str, date: &str, currency: &str) -> CheckedOffers {
    let mut checked = CheckedOffers { offers: Vec::new(), rejected: Vec::new() };
    for offer in &page.offers {
        match offer_mismatch(offer, origin, destination, date, currency) {
            None => checked.offers.push(offer.clone()),
            Some(reason) => checked.rejected.push(reason),
        }
    }
    checked
}

fn offer_mismatch(offer: &FliOffer, origin: &str, destination: &str, date: &str, currency: &str) -> Option<String> {
    let (Some(first), Some(last)) = (offer.legs.first(), offer.legs.last()) else {
        return Some("offer without legs".into());
    };
    if first.origin != origin || last.destination != destination {
        return Some(format!("airports {}-{}", first.origin, last.destination));
    }
    if !first.depart_local.starts_with(date) {
        return Some(format!("date {}", first.depart_local));
    }
    if offer.currency.as_deref() != Some(currency) {
        return Some(format!("currency {:?}", offer.currency));
    }
    let positive = offer.price.parse::<rust_decimal::Decimal>().map(|p| p > rust_decimal::Decimal::ZERO).unwrap_or(false);
    if !positive {
        return Some(format!("price {}", offer.price));
    }
    if offer.legs.iter().any(|l| l.airline.is_empty() || l.flight_number.is_empty()) {
        return Some("missing flight number".into());
    }
    None
}
