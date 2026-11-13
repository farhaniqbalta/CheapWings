//! Ranking views, order-compatible with `backend/src/cheapwings/engine/ranking.py`
//! (Python's stable sort: ties keep input order; Rust's `sort_by` is stable too).

use rust_decimal::Decimal;
use serde::Deserialize;
use std::str::FromStr;

/// The offer fields ranking reads. Enum values are the Python `.value` strings.
#[derive(Debug, Clone, PartialEq, Eq, Deserialize)]
pub struct RankOffer {
    pub id: String,
    pub price_status: String,
    pub hidden_city: String,
    pub comparison_status: String,
    pub amount: Option<String>,
}

fn tier(price_status: &str) -> u8 {
    match price_status {
        "repriced_exact" => 0,
        "recent_search" => 1,
        "indicative" => 2,
        _ => 3,
    }
}

fn priced<'a>(offers: impl Iterator<Item = &'a RankOffer>) -> Vec<(&'a RankOffer, Decimal)> {
    offers.filter_map(|o| Some((o, Decimal::from_str(o.amount.as_deref()?).ok()?))).collect()
}

/// Default view: hidden-city NO, eligible total known, comparable amount; by (tier, amount).
pub fn best_checked_deal(groups: &[Vec<RankOffer>]) -> Vec<String> {
    let mut picked = priced(
        groups
            .iter()
            .flatten()
            .filter(|o| o.hidden_city == "no" && o.comparison_status == "eligible_total_known"),
    );
    picked.sort_by(|a, b| (tier(&a.0.price_status), a.1).cmp(&(tier(&b.0.price_status), b.1)));
    picked.into_iter().map(|(o, _)| o.id.clone()).collect()
}

/// Alternate view: everything except confirmed hidden-city, by amount.
pub fn lowest_advertised(groups: &[Vec<RankOffer>]) -> Vec<String> {
    let mut picked = priced(groups.iter().flatten().filter(|o| o.hidden_city != "yes"));
    picked.sort_by(|a, b| a.1.cmp(&b.1));
    picked.into_iter().map(|(o, _)| o.id.clone()).collect()
}
