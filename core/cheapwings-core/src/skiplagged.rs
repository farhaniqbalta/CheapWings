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
    let message: Value =
        serde_json::from_str(rpc_json).map_err(|_| SkiplaggedError::SchemaChanged)?;
    if message.get("error").is_some() {
        return Err(SkiplaggedError::ProviderUnavailable);
    }
    let result = message
        .get("result")
        .ok_or(SkiplaggedError::SchemaChanged)?;
    if result.get("isError").and_then(Value::as_bool) == Some(true) {
        return Err(SkiplaggedError::ProviderUnavailable);
    }
    if let Some(structured) = result
        .get("structuredContent")
        .filter(|v| v.get("flights").is_some())
    {
        return serde_json::to_string(structured).map_err(|_| SkiplaggedError::SchemaChanged);
    }
    for block in result
        .get("content")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
    {
        if block.get("type").and_then(Value::as_str) != Some("text") {
            continue;
        }
        let Some(text) = block.get("text").and_then(Value::as_str) else {
            continue;
        };
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
    let parsed = Decimal::from_str(&text)
        .or_else(|_| Decimal::from_scientific(&text))
        .map_err(|_| InvalidPrice)?;
    if parsed.is_sign_negative() && !parsed.is_zero() {
        return Err(InvalidPrice);
    }
    Ok(text)
}

/// `aware_iso` for "YYYY-MM-DDTHH:MM[:SS[.f]]±HH:MM|Z": (naive local minute text, seconds since epoch UTC).
fn zoned(value: &Value) -> Result<(String, i64), SkiplaggedError> {
    let text = value.as_str().ok_or(SchemaChanged)?;
    let (local, offset_seconds) = if let Some(base) = text.strip_suffix('Z') {
        (base, 0)
    } else if let Some(index) = text
        .get(10..)
        .and_then(|tail| tail.find(['+', '-']))
        .map(|i| i + 10)
    {
        let (base, off) = text.split_at(index);
        let sign = if off.starts_with('-') { -1 } else { 1 };
        let whole = off[1..]
            .split(['.', ','])
            .next()
            .unwrap_or_default()
            .replace(':', "");
        if !matches!(whole.len(), 2 | 4 | 6) || !whole.bytes().all(|b| b.is_ascii_digit()) {
            return Err(SchemaChanged);
        }
        let part = |i| {
            whole
                .get(i..i + 2)
                .and_then(|part| part.parse::<i64>().ok())
                .unwrap_or(0)
        };
        let seconds = part(0) * 3600 + part(2) * 60 + part(4);
        if seconds >= 86400 {
            return Err(SchemaChanged);
        }
        (base, sign * seconds)
    } else {
        return if naive_parts(text).is_some() {
            Err(MissingSegments)
        } else {
            Err(SchemaChanged)
        };
    };
    let (y, mo, d, h, mi) = naive_parts(local).ok_or(SchemaChanged)?;
    let sec = if local.as_bytes().get(16) == Some(&b':') {
        local
            .get(17..19)
            .and_then(|s| s.parse::<i64>().ok())
            .ok_or(SchemaChanged)?
    } else {
        0
    };
    let utc = (days_from_civil(y, mo, d) * 1440 + h * 60 + mi) * 60 + sec - offset_seconds;
    Ok((format!("{y:04}-{mo:02}-{d:02}T{h:02}:{mi:02}"), utc))
}

fn naive_parts(text: &str) -> Option<(i64, i64, i64, i64, i64)> {
    let b = text.as_bytes();
    if b.len() < 16
        || b[4] != b'-'
        || b[7] != b'-'
        || !matches!(b[10], b'T' | b' ')
        || b[13] != b':'
    {
        return None;
    }
    let n = |r: std::ops::Range<usize>| text.get(r)?.parse::<i64>().ok();
    let (y, mo, d, h, mi) = (n(0..4)?, n(5..7)?, n(8..10)?, n(11..13)?, n(14..16)?);
    ((1..=12).contains(&mo) && (1..=31).contains(&d) && h < 24 && mi < 60)
        .then_some((y, mo, d, h, mi))
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
    let cleaned = link
        .trim_start_matches(|c: char| c <= ' ')
        .replace(['\t', '\n', '\r'], "");
    let rest = cleaned.strip_prefix("https://").or_else(|| {
        cleaned
            .get(..8)
            .filter(|s| s.eq_ignore_ascii_case("https://"))
            .map(|_| &cleaned[8..])
    })?;
    let authority = rest.split(['/', '?', '#']).next().unwrap_or("");
    let host = authority
        .rsplit('@')
        .next()
        .unwrap_or("")
        .split(':')
        .next()
        .unwrap_or("");
    host.eq_ignore_ascii_case("skiplagged.com")
        .then(|| link.to_owned())
}

#[derive(Serialize)]
struct Card<'a> {
    id: &'a Value,
    depart: &'a Value,
    arrive: &'a Value,
    usd: String,
    stops: u64,
    carrier: Option<&'a str>,
    link: Option<String>,
    #[serde(skip)]
    depart_local: String,
    #[serde(skip)]
    arrive_local: String,
    #[serde(skip)]
    minutes: i64,
}

fn cards(payload: &Value) -> Result<&[Value], SkiplaggedError> {
    payload
        .get("flights")
        .and_then(Value::as_array)
        .map(Vec::as_slice)
        .ok_or(SchemaChanged)
}

fn decode_card<'a>(
    card: &'a Value,
    origin: &str,
    destination: &str,
    date: &str,
) -> Result<Card<'a>, SkiplaggedError> {
    let field = |path| card.pointer(path).ok_or(SchemaChanged);
    let depart = field("/departure/dateTime")?;
    let arrive = field("/arrival/dateTime")?;
    let (depart_local, depart_utc) = zoned(depart)?;
    let (arrive_local, arrive_utc) = zoned(arrive)?;
    if field("/departure/airport")?.as_str() != Some(origin)
        || field("/arrival/airport")?.as_str() != Some(destination)
        || &depart_local[..10] != date
    {
        return Err(SchemaChanged);
    }
    let usd = decimal_text(field("/price/usdAmount")?)?;
    let stops = field("/layovers")?
        .as_number()
        .filter(|n| !n.to_string().contains(['.', 'e', 'E']))
        .and_then(|n| n.as_u64())
        .ok_or(SchemaChanged)?;
    Ok(Card {
        id: field("/id")?,
        depart,
        arrive,
        usd,
        stops,
        carrier: card
            .get("airlines")
            .and_then(Value::as_str)
            .map(crate::python_strip)
            .filter(|name| !name.is_empty()),
        link: skiplagged_link(card.get("deepLink")),
        depart_local,
        arrive_local,
        minutes: (arrive_utc - depart_utc).div_euclid(60),
    })
}

pub fn web_payload(
    json: &str,
    origin: &str,
    destination: &str,
    date: &str,
) -> Result<String, SkiplaggedError> {
    let payload: Value = serde_json::from_str(json).map_err(|_| SchemaChanged)?;
    let flights: Vec<Value> = cards(&payload)?
        .iter()
        .map(|card| match decode_card(card, origin, destination, date) {
            Ok(record) => serde_json::json!(record),
            Err(err) => serde_json::json!({"error": err.code()}),
        })
        .collect();
    Ok(serde_json::json!({
        "flights": flights,
        "pricing": payload.get("pricing").cloned().unwrap_or_else(|| serde_json::json!({})),
        "complete": completeness(&payload),
    })
    .to_string())
}

fn completeness(payload: &Value) -> Option<bool> {
    payload
        .get("pagination")
        .and_then(|p| p.get("hasMoreResults"))
        .and_then(Value::as_bool)
        .map(|more| !more)
}

pub fn skiplagged_parse(
    json: &str,
    origin: &str,
    destination: &str,
    date: &str,
    display_currency: &str,
) -> Result<SkiplaggedPage, SkiplaggedError> {
    let payload: Value = serde_json::from_str(json).map_err(|_| SchemaChanged)?;
    let complete = completeness(&payload);
    let pricing = payload.get("pricing");
    let mut offers = Vec::new();
    for card in cards(&payload)? {
        let card = decode_card(card, origin, destination, date)?;
        let usd = card.usd;
        let (comparable, fx) = if display_currency == "USD" {
            (Some(usd.clone()), None)
        } else {
            let rate_as_of = pricing
                .and_then(|p| p.get("rateAsOf"))
                .and_then(Value::as_str)
                .filter(|s| !s.is_empty());
            match (
                pricing
                    .and_then(|p| p.get("currency"))
                    .and_then(Value::as_str),
                rate_as_of,
            ) {
                (Some(currency), Some(as_of)) if currency == display_currency => {
                    let rate =
                        decimal_text(pricing.and_then(|p| p.get("rate")).ok_or(SchemaChanged)?)?;
                    let converted =
                        fx_convert(&usd, &rate, display_currency).map_err(|_| SchemaChanged)?;
                    (
                        Some(converted),
                        Some(FxNote {
                            rate,
                            as_of: as_of.to_owned(),
                            to_currency: display_currency.to_owned(),
                        }),
                    )
                }
                _ => (None, None),
            }
        };
        offers.push(SourceOffer {
            provider: "skiplagged".into(),
            id: stable_id(card.id),
            origin: origin.into(),
            destination: destination.into(),
            depart_local: card.depart_local,
            arrive_local: card.arrive_local,
            minutes: Some(card.minutes),
            stops: card.stops as u32,
            carriers: card.carrier.into_iter().map(str::to_owned).collect(),
            legs: Vec::new(),
            price_original: usd,
            currency_original: "USD".into(),
            price_comparable: comparable,
            fx,
            link: card.link,
            hidden_city: "no".into(),
        });
    }
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
        currency_original: offer
            .currency
            .clone()
            .unwrap_or_else(|| display_currency.to_owned()),
        price_comparable: Some(offer.price.clone()),
        fx: None,
        link: None,
        hidden_city: "unknown".into(),
    }
}
