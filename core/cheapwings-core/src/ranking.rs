//! Ranking views, order-compatible with `backend/src/cheapwings/engine/ranking.py`
//! (Python's stable sort: ties keep input order; Rust's `sort_by` is stable too).

use serde::Deserialize;
use std::cmp::Ordering;

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

// Ranking compares exact source values; fixed-precision money arithmetic may round them.
struct ExactAmount { negative: bool, digits: Vec<u8>, exponent: i64 }

impl ExactAmount {
    fn parse(text: &str) -> Option<Self> {
        let (negative, text) = if let Some(rest) = text.strip_prefix('-') { (true, rest) } else { (false, text.strip_prefix('+').unwrap_or(text)) };
        let (mantissa, exponent) = match text.split_once(['e', 'E']) {
            Some((m, e)) => (m, e.parse::<i64>().ok()?),
            None => (text, 0),
        };
        let (whole, fraction) = mantissa.split_once('.').unwrap_or((mantissa, ""));
        if whole.is_empty() && fraction.is_empty() { return None; }
        if !whole.bytes().chain(fraction.bytes()).all(|b| b.is_ascii_digit()) { return None; }
        let mut digits: Vec<u8> = whole.bytes().chain(fraction.bytes()).skip_while(|b| *b == b'0').collect();
        if digits.is_empty() { return Some(Self { negative: false, digits: vec![b'0'], exponent: 0 }); }
        let mut exponent = exponent.checked_sub(fraction.len() as i64)?;
        while digits.last() == Some(&b'0') { digits.pop(); exponent = exponent.checked_add(1)?; }
        Some(Self { negative, digits, exponent })
    }

    fn cmp(&self, other: &Self) -> Ordering {
        let zero = |value: &Self| value.digits == [b'0'];
        if zero(self) && zero(other) { return Ordering::Equal; }
        if self.negative != other.negative { return self.negative.cmp(&other.negative).reverse(); }
        let magnitude = if zero(self) { Ordering::Less } else if zero(other) { Ordering::Greater } else {
            let place = (self.digits.len() as i128 + self.exponent as i128).cmp(&(other.digits.len() as i128 + other.exponent as i128));
            place.then_with(|| self.digits.iter().copied().chain(std::iter::repeat(b'0')).take(self.digits.len().max(other.digits.len()))
                .cmp(other.digits.iter().copied().chain(std::iter::repeat(b'0')).take(self.digits.len().max(other.digits.len()))))
        };
        if self.negative { magnitude.reverse() } else { magnitude }
    }
}

fn priced<'a>(offers: impl Iterator<Item = &'a RankOffer>) -> Vec<(&'a RankOffer, ExactAmount)> {
    offers.filter_map(|o| Some((o, ExactAmount::parse(o.amount.as_deref()?)?))).collect()
}

/// Default view: hidden-city NO, eligible total known, comparable amount; by (tier, amount).
pub fn best_checked_deal(groups: &[Vec<RankOffer>]) -> Vec<String> {
    let mut picked = priced(
        groups
            .iter()
            .flatten()
            .filter(|o| o.hidden_city == "no" && o.comparison_status == "eligible_total_known"),
    );
    picked.sort_by(|a, b| tier(&a.0.price_status).cmp(&tier(&b.0.price_status)).then_with(|| a.1.cmp(&b.1)));
    picked.into_iter().map(|(o, _)| o.id.clone()).collect()
}

/// Alternate view: everything except confirmed hidden-city, by amount.
pub fn lowest_advertised(groups: &[Vec<RankOffer>]) -> Vec<String> {
    let mut picked = priced(groups.iter().flatten().filter(|o| o.hidden_city != "yes"));
    picked.sort_by(|a, b| a.1.cmp(&b.1));
    picked.into_iter().map(|(o, _)| o.id.clone()).collect()
}
