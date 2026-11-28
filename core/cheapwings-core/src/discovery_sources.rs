//! P7.4 discovery sources: which calls a Discover run makes, and Skiplagged "anywhere" replies
//! mapped to `DiscoveryObservation`s (docs/log/p7.1.md "Adapter mapping").

use crate::discovery::{
    validate, DiscoveryError, DiscoveryObservation, DiscoveryQuery, FxRate, ValidQuery,
};
use crate::planning::{civil_from_days, PlanError};
use crate::skiplagged::{skiplagged_link, tool_payload, SkiplaggedError};
use serde::{Deserialize, Serialize};
use serde_json::Value;

/// Owner-approved (2026-11-22): origins × days per Discover run.
pub const MAX_DISCOVERY_CALLS: u32 = 31;

/// One anywhere call: every destination from `origin` on `date`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DiscoveryCall {
    pub origin: String,
    pub date: String,
}

/// Origins in query order (normalized, de-duplicated), then dates ascending.
pub fn discovery_calls(query: &DiscoveryQuery) -> Result<Vec<DiscoveryCall>, DiscoveryError> {
    let ValidQuery {
        origins,
        from,
        through,
        ..
    } = validate(query)?;
    let total = origins.len() as u64 * (through - from + 1) as u64;
    if total > u64::from(MAX_DISCOVERY_CALLS) {
        return Err(PlanError::TooMany {
            combinations: u32::try_from(total).unwrap_or(u32::MAX),
            max: MAX_DISCOVERY_CALLS,
        }
        .into());
    }
    Ok(origins
        .iter()
        .flat_map(|origin| {
            (from..=through).map(move |day| {
                let (y, m, d) = civil_from_days(day);
                DiscoveryCall {
                    origin: origin.clone(),
                    date: format!("{y:04}-{m:02}-{d:02}"),
                }
            })
        })
        .collect())
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AnywherePage {
    pub observations: Vec<DiscoveryObservation>,
    /// `[{USD, pricing.rate}]`, or empty when the reply has no rate.
    pub fx: Vec<FxRate>,
    /// Rows without a USD price: dropped, counted for coverage.
    pub unpriced: u32,
}

fn lexeme(value: &Value) -> Option<String> {
    match value {
        Value::Number(n) => Some(n.to_string()),
        Value::String(s) => Some(s.clone()),
        _ => None,
    }
}

/// Drops `utm_*` query parameters (tracking), keeping the rest in order.
fn strip_utm(link: String) -> String {
    let Some((base, query)) = link.split_once('?') else {
        return link;
    };
    let kept: Vec<&str> = query
        .split('&')
        .filter(|p| !p.starts_with("utm_"))
        .collect();
    if kept.is_empty() {
        base.to_owned()
    } else {
        format!("{base}?{}", kept.join("&"))
    }
}

/// A raw `sk_destinations_anywhere` JSON-RPC reply → observations for `origin` on `depart`.
pub fn skiplagged_anywhere(
    rpc_json: &str,
    origin: &str,
    depart: &str,
    fetched_at: &str,
) -> Result<AnywherePage, SkiplaggedError> {
    let payload: Value = serde_json::from_str(&tool_payload(rpc_json, "results")?)
        .map_err(|_| SkiplaggedError::SchemaChanged)?;
    let rows = payload
        .get("results")
        .and_then(Value::as_array)
        .ok_or(SkiplaggedError::SchemaChanged)?;
    let mut page = AnywherePage {
        observations: Vec::new(),
        fx: Vec::new(),
        unpriced: 0,
    };
    if let Some(rate) = payload.pointer("/pricing/rate").and_then(lexeme) {
        page.fx.push(FxRate {
            currency: "USD".into(),
            rate,
        });
    }
    for row in rows {
        let Some(amount) = row.pointer("/price/usdAmount").and_then(lexeme) else {
            page.unpriced += 1;
            continue;
        };
        let standard = row.get("flightType").and_then(Value::as_str) == Some("Standard");
        page.observations.push(DiscoveryObservation {
            origin: origin.to_owned(),
            // Missing airport passes through as "" and is counted invalid by selection.
            destination: row
                .pointer("/destination/airport")
                .and_then(Value::as_str)
                .unwrap_or("")
                .to_owned(),
            departure_date: Some(depart.to_owned()),
            amount,
            currency: "USD".into(),
            source_id: "skiplagged".into(),
            observed_at: None,
            fetched_at: fetched_at.to_owned(),
            price_kind: "indicative".into(),
            hidden_city: if standard { "no" } else { "unknown" }.into(),
            source_reference: skiplagged_link(row.get("deepLink")).map(strip_utm),
        });
    }
    Ok(page)
}

#[derive(Deserialize)]
struct AnywhereInput {
    rpc_json: String,
    origin: String,
    depart: String,
    fetched_at: String,
}

/// JSON in/out for PyO3: `{rpc_json, origin, depart, fetched_at}` → `AnywherePage`; errors are `"code: detail"`.
pub fn anywhere_web_payload(payload: &str) -> Result<String, String> {
    let i: AnywhereInput =
        serde_json::from_str(payload).map_err(|e| format!("invalid_payload: {e}"))?;
    let page = skiplagged_anywhere(&i.rpc_json, &i.origin, &i.depart, &i.fetched_at)
        .map_err(|e| format!("{}: {e}", e.code()))?;
    Ok(serde_json::to_string(&page).expect("page serializes"))
}

/// JSON in/out for PyO3: a `DiscoveryQuery` → `[DiscoveryCall]`; errors are `"code: detail"`.
pub fn calls_web_payload(payload: &str) -> Result<String, String> {
    let query: DiscoveryQuery =
        serde_json::from_str(payload).map_err(|e| format!("invalid_payload: {e}"))?;
    let calls = discovery_calls(&query).map_err(|e| format!("{}: {e}", e.code()))?;
    Ok(serde_json::to_string(&calls).expect("calls serialize"))
}
