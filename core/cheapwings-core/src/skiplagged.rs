//! Skiplagged `sk_flights_search` results → provider-neutral offers. Port of
//! `providers/skiplagged.py` `normalize()`: same checks, exact decimals (the raw MCP JSON text is
//! parsed with arbitrary precision, like `json_payload(parse_float=Decimal)`), display-only FX.

use std::str::FromStr;

use rust_decimal::Decimal;
use serde::Serialize;
use serde_json::Value;
use sha2::{Digest, Sha256};

use crate::fli::{FliLeg, FliOffer};
use crate::money::fx_convert;

/// Display-only conversion evidence (Skiplagged's own rate and its date).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, serde::Deserialize)]
pub struct FxNote {
    pub rate: String,
    pub as_of: String,
    pub to_currency: String,
}

/// One offer from any source. `legs` is empty when the source gives no per-flight detail
/// (Skiplagged); `price_comparable` is in the display currency, `None` when it cannot be compared.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, serde::Deserialize)]
pub struct SourceOffer {
    pub provider: String,
    pub id: String,
    pub origin: String,
    pub destination: String,
    /// Naive local "YYYY-MM-DDTHH:MM" at each airport.
    pub depart_local: String,
    pub arrive_local: String,
    /// Door-to-door minutes when the source gives zoned times (Skiplagged); Fli computes its own.
    pub minutes: Option<i64>,
    pub stops: u32,
    pub carriers: Vec<String>,
    pub legs: Vec<FliLeg>,
    pub price_original: String,
    pub currency_original: String,
    pub price_comparable: Option<String>,
    pub fx: Option<FxNote>,
    pub link: Option<String>,
    /// `no | yes | unknown` (Skiplagged: hidden-city excluded by the request).
    pub hidden_city: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SkiplaggedPage {
    pub offers: Vec<SourceOffer>,
    /// `Some(false)` when Skiplagged says more results exist; `None` when it does not say.
    pub complete: Option<bool>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SkiplaggedError {
    SchemaChanged,
    InvalidPrice,
    MissingSegments,
    ProviderUnavailable,
}

impl std::fmt::Display for SkiplaggedError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(match self {
            Self::SchemaChanged => "response does not match the expected Skiplagged shape",
            Self::InvalidPrice => "price is missing, negative or not a number",
            Self::MissingSegments => "a time has no UTC offset",
            Self::ProviderUnavailable => "Skiplagged returned a tool error",
        })
    }
}

impl std::error::Error for SkiplaggedError {}

impl SkiplaggedError {
    pub fn code(&self) -> &'static str {
        match self {
            Self::SchemaChanged => "schema_changed",
            Self::InvalidPrice => "invalid_price",
            Self::MissingSegments => "missing_segments",
            Self::ProviderUnavailable => "provider_unavailable",
        }
    }
}

/// The `sk_flights_search` payload (exact JSON text) from a raw JSON-RPC `tools/call` reply, in
/// `mcp_search`'s order: exact structured content, then a text block holding a JSON object with
/// `flights`. A tool error or JSON-RPC error is `provider_unavailable`.
pub fn skiplagged_tool_payload(rpc_json: &str) -> Result<String, SkiplaggedError> {
    let message: Value = serde_json::from_str(rpc_json).map_err(|_| SkiplaggedError::SchemaChanged)?;
    if message.get("error").is_some() {
        return Err(SkiplaggedError::ProviderUnavailable);
    }
    let result = message.get("result").ok_or(SkiplaggedError::SchemaChanged)?;
    if result.get("isError").and_then(Value::as_bool) == Some(true) {
        return Err(SkiplaggedError::ProviderUnavailable);
    }
    if let Some(structured) = result.get("structuredContent").filter(|v| v.get("flights").is_some()) {
        return serde_json::to_string(structured).map_err(|_| SkiplaggedError::SchemaChanged);
    }
    for block in result.get("content").and_then(Value::as_array).into_iter().flatten() {
        if block.get("type").and_then(Value::as_str) != Some("text") {
            continue;
        }
        let Some(text) = block.get("text").and_then(Value::as_str) else { continue };
        if let Ok(parsed) = serde_json::from_str::<Value>(text) {
            if parsed.is_object() && parsed.get("flights").is_some() {
                return Ok(text.to_owned());
            }
        }
    }
    Err(SkiplaggedError::SchemaChanged)
}

use SkiplaggedError::*;

/// `providers/common.decimal_value`: a JSON number or string, finite and non-negative.
fn decimal_text(value: &Value) -> Result<String, SkiplaggedError> {
    let text = match value {
        Value::Number(n) => n.to_string(),
        Value::String(s) => s.clone(),
        _ => return Err(InvalidPrice),
    };
    let parsed = Decimal::from_str(&text).or_else(|_| Decimal::from_scientific(&text)).map_err(|_| InvalidPrice)?;
    if parsed.is_sign_negative() && !parsed.is_zero() {
        return Err(InvalidPrice);
    }
    Ok(text)
}

/// `aware_iso` for "YYYY-MM-DDTHH:MM[:SS[.f]]±HH:MM|Z": (naive local minute text, seconds since epoch UTC).
fn zoned(value: &Value) -> Result<(String, i64), SkiplaggedError> {
    let text = value.as_str().ok_or(SchemaChanged)?;
    let (local, offset_min) = if let Some(base) = text.strip_suffix('Z') {
        (base, 0)
    } else if text.len() > 6 && matches!(text.as_bytes()[text.len() - 6], b'+' | b'-') && text.as_bytes()[text.len() - 3] == b':' {
        let (base, off) = text.split_at(text.len() - 6);
        let sign = if off.starts_with('-') { -1 } else { 1 };
        let hours: i64 = off[1..3].parse().map_err(|_| SchemaChanged)?;
        let mins: i64 = off[4..6].parse().map_err(|_| SchemaChanged)?;
        (base, sign * (hours * 60 + mins))
    } else {
        // Python parses a naive time fine, then rejects it for having no offset.
        return if naive_parts(text).is_some() { Err(MissingSegments) } else { Err(SchemaChanged) };
    };
    let (y, mo, d, h, mi) = naive_parts(local).ok_or(SchemaChanged)?;
    let sec = if local.as_bytes().get(16) == Some(&b':') { local.get(17..19).and_then(|s| s.parse::<i64>().ok()).ok_or(SchemaChanged)? } else { 0 };
    let utc = (days_from_civil(y, mo, d) * 1440 + h * 60 + mi - offset_min) * 60 + sec;
    Ok((format!("{y:04}-{mo:02}-{d:02}T{h:02}:{mi:02}"), utc))
}

fn naive_parts(text: &str) -> Option<(i64, i64, i64, i64, i64)> {
    let b = text.as_bytes();
    if b.len() < 16 || b[4] != b'-' || b[7] != b'-' || !matches!(b[10], b'T' | b' ') || b[13] != b':' {
        return None;
    }
    let n = |r: std::ops::Range<usize>| text.get(r)?.parse::<i64>().ok();
    let (y, mo, d, h, mi) = (n(0..4)?, n(5..7)?, n(8..10)?, n(11..13)?, n(14..16)?);
    ((1..=12).contains(&mo) && (1..=31).contains(&d) && h < 24 && mi < 60).then_some((y, mo, d, h, mi))
}

/// Days since 1970-01-01 (Howard Hinnant's civil-from-days inverse).
fn days_from_civil(y: i64, m: i64, d: i64) -> i64 {
    let y = if m <= 2 { y - 1 } else { y };
    let era = y.div_euclid(400);
    let yoe = y - era * 400;
    let doy = (153 * (m + if m > 2 { -3 } else { 9 }) + 2) / 5 + d - 1;
    let doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    era * 146_097 + doe - 719_468
}

/// `stable_id(card_id)` = sha256 of Python `json.dumps([card_id])` (ASCII-escaped, ", " separators).
fn stable_id(id: &Value) -> String {
    let mut ascii = String::new();
    for ch in serde_json::to_string(id).unwrap_or_default().chars() {
        if ch.is_ascii() {
            ascii.push(ch);
        } else {
            let mut buf = [0u16; 2];
            for unit in ch.encode_utf16(&mut buf) {
                ascii.push_str(&format!("\\u{unit:04x}"));
            }
        }
    }
    let digest = Sha256::digest(format!("[{ascii}]").as_bytes());
    digest.iter().map(|b| format!("{b:02x}")).collect()
}

/// `urlsplit(link)`: keep only https links whose host is exactly skiplagged.com.
fn skiplagged_link(value: Option<&Value>) -> Option<String> {
    let link = value?.as_str()?;
    let rest = link.strip_prefix("https://").or_else(|| link.get(..8).filter(|s| s.eq_ignore_ascii_case("https://")).map(|_| &link[8..]))?;
    let authority = rest.split(['/', '?', '#']).next().unwrap_or("");
    let host = authority.rsplit('@').next().unwrap_or("").split(':').next().unwrap_or("");
    host.eq_ignore_ascii_case("skiplagged.com").then(|| link.to_owned())
}

pub fn skiplagged_parse(json: &str, origin: &str, destination: &str, date: &str, display_currency: &str) -> Result<SkiplaggedPage, SkiplaggedError> {
    let payload: Value = serde_json::from_str(json).map_err(|_| SchemaChanged)?;
    let cards = payload.get("flights").ok_or(SchemaChanged)?.as_array().ok_or(SchemaChanged)?;
    let pricing = payload.get("pricing");
    let mut offers = Vec::new();
    for card in cards {
        let (depart_local, depart_utc) = zoned(card.get("departure").and_then(|d| d.get("dateTime")).ok_or(SchemaChanged)?)?;
        let (arrive_local, arrive_utc) = zoned(card.get("arrival").and_then(|a| a.get("dateTime")).ok_or(SchemaChanged)?)?;
        let airport = |side: &str| card.get(side).and_then(|s| s.get("airport")).and_then(Value::as_str);
        if airport("departure") != Some(origin) || airport("arrival") != Some(destination) || &depart_local[..10] != date {
            return Err(SchemaChanged);
        }
        let usd = decimal_text(card.get("price").ok_or(SchemaChanged)?.get("usdAmount").ok_or(SchemaChanged)?)?;
        let (comparable, fx) = if display_currency == "USD" {
            (Some(usd.clone()), None)
        } else {
            let rate_as_of = pricing.and_then(|p| p.get("rateAsOf")).and_then(Value::as_str).filter(|s| !s.is_empty());
            match (pricing.and_then(|p| p.get("currency")).and_then(Value::as_str), rate_as_of) {
                (Some(currency), Some(as_of)) if currency == display_currency => {
                    let rate = decimal_text(pricing.and_then(|p| p.get("rate")).ok_or(SchemaChanged)?)?;
                    let converted = fx_convert(&usd, &rate, display_currency).map_err(|_| SchemaChanged)?;
                    (Some(converted), Some(FxNote { rate, as_of: as_of.to_owned(), to_currency: display_currency.to_owned() }))
                }
                _ => (None, None),
            }
        };
        let stops = match card.get("layovers") {
            Some(Value::Number(n)) if n.is_u64() && !n.to_string().contains(['.', 'e', 'E']) => n.as_u64().unwrap() as u32,
            _ => return Err(SchemaChanged),
        };
        let carriers = card
            .get("airlines")
            .and_then(Value::as_str)
            .map(str::trim)
            .filter(|s| !s.is_empty())
            .map(|s| vec![s.to_owned()])
            .unwrap_or_default();
        offers.push(SourceOffer {
            provider: "skiplagged".into(),
            id: stable_id(card.get("id").ok_or(SchemaChanged)?),
            origin: origin.into(),
            destination: destination.into(),
            depart_local,
            arrive_local,
            // Python: int((arrive - depart).total_seconds() // 60).
            minutes: Some((arrive_utc - depart_utc).div_euclid(60)),
            stops,
            carriers,
            legs: Vec::new(),
            price_original: usd,
            currency_original: "USD".into(),
            price_comparable: comparable,
            fx,
            link: skiplagged_link(card.get("deepLink")),
            hidden_city: "no".into(),
        });
    }
    let complete = payload.get("pagination").and_then(|p| p.get("hasMoreResults")).and_then(Value::as_bool).map(|more| !more);
    Ok(SkiplaggedPage { offers, complete })
}

/// A Fli offer as a provider-neutral offer (prices are already in the requested currency).
pub fn fli_source_offer(offer: &FliOffer, id: &str, display_currency: &str) -> SourceOffer {
    let first = offer.legs.first();
    let last = offer.legs.last();
    let mut carriers: Vec<String> = Vec::new();
    for leg in &offer.legs {
        if !carriers.contains(&leg.airline) {
            carriers.push(leg.airline.clone());
        }
    }
    SourceOffer {
        provider: "fli".into(),
        id: id.into(),
        origin: first.map(|l| l.origin.clone()).unwrap_or_default(),
        destination: last.map(|l| l.destination.clone()).unwrap_or_default(),
        depart_local: first.map(|l| l.depart_local.clone()).unwrap_or_default(),
        arrive_local: last.map(|l| l.arrive_local.clone()).unwrap_or_default(),
        minutes: None,
        stops: offer.legs.len().saturating_sub(1) as u32,
        carriers,
        legs: offer.legs.clone(),
        price_original: offer.price.clone(),
        currency_original: offer.currency.clone().unwrap_or_else(|| display_currency.to_owned()),
        price_comparable: Some(offer.price.clone()),
        fx: None,
        link: None,
        hidden_city: "unknown".into(),
    }
}
