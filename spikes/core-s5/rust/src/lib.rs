//! S5 (B): Rust port of money.py arithmetic, compute_fingerprint and ranking.py, checked
//! against Python-generated fixtures. Exposed to Swift via UniFFI.

use rust_decimal::prelude::ToPrimitive;
use rust_decimal::{Decimal, RoundingStrategy};
use serde::Deserialize;
use sha2::{Digest, Sha256};
use std::str::FromStr;
use std::time::Instant;

uniffi::setup_scaffolding!();

// ---------- money (same rules as spikes/money-pyo3) ----------

const EXPONENTS: &[(&str, u32)] = &[
    ("IDR", 0), ("JPY", 0), ("KRW", 0), ("VND", 0),
    ("USD", 2), ("AUD", 2), ("EUR", 2), ("GBP", 2), ("CAD", 2), ("SGD", 2), ("MYR", 2),
    ("INR", 2), ("CNY", 2), ("HKD", 2), ("NZD", 2), ("CHF", 2), ("THB", 2), ("PHP", 2),
    ("BRL", 2), ("MXN", 2), ("CZK", 2), ("DKK", 2), ("SEK", 2), ("PLN", 2), ("RON", 2),
    ("TRY", 2), ("TWD", 2), ("UAH", 2),
];

fn exponent(currency: &str) -> Option<u32> {
    let code = currency.to_uppercase();
    EXPONENTS.iter().find(|(c, _)| *c == code).map(|(_, e)| *e)
}

fn parse(text: &str) -> Option<Decimal> {
    if text.contains(['e', 'E']) { Decimal::from_scientific(text).ok() } else { Decimal::from_str(text).ok() }
}

pub fn fx_convert(amount: &str, rate: &str, currency: &str) -> Option<String> {
    let exp = exponent(currency)?;
    let product = parse(amount)?.checked_mul(parse(rate)?)?;
    let mut rounded = product.round_dp_with_strategy(exp, RoundingStrategy::MidpointNearestEven);
    rounded.rescale(exp);
    let text = rounded.to_string();
    Some(if product.is_sign_negative() && rounded.is_zero() { format!("-{text}") } else { text })
}

pub fn from_minor_units(minor: i128, currency: &str) -> Option<String> {
    Decimal::try_from_i128_with_scale(minor, exponent(currency)?).ok().map(|d| d.to_string())
}

pub fn as_minor_units(amount: &str, currency: &str) -> Option<String> {
    let scaled = parse(amount)?.checked_mul(Decimal::from(10u64.pow(exponent(currency)?)))?;
    if !scaled.fract().is_zero() {
        return None;
    }
    scaled.trunc().to_i128().map(|v| v.to_string())
}

// ---------- fingerprint ----------

#[derive(Deserialize)]
pub struct Instant8 { y: i32, mo: u32, d: u32, h: u32, mi: u32, s: u32, us: u32, offset: i32 }

#[derive(Deserialize)]
pub struct Segment {
    ordinal: u32, marketing: String, operating: String, flight: String,
    origin: String, destination: String, depart: Instant8, arrive: Instant8,
}

/// Byte-identical to Python `datetime.isoformat()` for an aware datetime.
fn isoformat(t: &Instant8) -> String {
    let mut out = format!("{:04}-{:02}-{:02}T{:02}:{:02}:{:02}", t.y, t.mo, t.d, t.h, t.mi, t.s);
    if t.us != 0 {
        out += &format!(".{:06}", t.us);
    }
    let sign = if t.offset < 0 { '-' } else { '+' };
    let off = t.offset.unsigned_abs();
    out += &format!("{sign}{:02}:{:02}", off / 3600, off % 3600 / 60);
    if off % 60 != 0 {
        out += &format!(":{:02}", off % 60);
    }
    out
}

pub fn fingerprint(segments: &[Segment]) -> String {
    let canonical = segments
        .iter()
        .map(|s| {
            [s.ordinal.to_string(), s.marketing.clone(), s.operating.clone(), s.flight.clone(),
             s.origin.clone(), s.destination.clone(), isoformat(&s.depart), isoformat(&s.arrive)]
                .join(",")
        })
        .collect::<Vec<_>>()
        .join("|");
    Sha256::digest(canonical.as_bytes()).iter().map(|b| format!("{b:02x}")).collect()
}

// ---------- ranking ----------

#[derive(Deserialize)]
pub struct Offer { id: String, price_status: String, hidden_city: String, comparison_status: String, amount: Option<String> }

fn tier(status: &str) -> u8 {
    match status { "repriced_exact" => 0, "recent_search" => 1, "indicative" => 2, _ => 3 }
}

/// `best_checked_deal`: safe + comparable only, by (tier, amount); stable like Python's sort.
pub fn best_checked_deal(groups: &[Vec<Offer>]) -> Vec<String> {
    let mut picked: Vec<(&Offer, Decimal)> = groups.iter().flatten()
        .filter(|o| o.hidden_city == "no" && o.comparison_status == "eligible_total_known")
        .filter_map(|o| Some((o, parse(o.amount.as_deref()?)?)))
        .collect();
    picked.sort_by(|a, b| (tier(&a.0.price_status), a.1).cmp(&(tier(&b.0.price_status), b.1)));
    picked.into_iter().map(|(o, _)| o.id.clone()).collect()
}

/// `lowest_advertised`: everything except confirmed hidden-city, by amount; stable.
pub fn lowest_advertised(groups: &[Vec<Offer>]) -> Vec<String> {
    let mut picked: Vec<(&Offer, Decimal)> = groups.iter().flatten()
        .filter(|o| o.hidden_city != "yes")
        .filter_map(|o| Some((o, parse(o.amount.as_deref()?)?)))
        .collect();
    picked.sort_by(|a, b| a.1.cmp(&b.1));
    picked.into_iter().map(|(o, _)| o.id.clone()).collect()
}

// ---------- fixtures + bench ----------

#[derive(Deserialize)]
struct MoneyCase { op: String, amount: Option<String>, rate: Option<String>, minor: Option<String>, currency: String, expect: Option<String> }
#[derive(Deserialize)]
struct FingerprintCase { segments: Vec<Segment>, expect: String }
#[derive(Deserialize)]
struct RankingCase { groups: Vec<Vec<Offer>>, best: Vec<String>, lowest: Vec<String> }
#[derive(Deserialize)]
struct Fixtures { money: Vec<MoneyCase>, fingerprint: Vec<FingerprintCase>, ranking: Vec<RankingCase> }

fn money_result(c: &MoneyCase) -> Option<String> {
    match c.op.as_str() {
        "fx" => fx_convert(c.amount.as_deref()?, c.rate.as_deref()?, &c.currency),
        "from_minor" => from_minor_units(c.minor.as_deref()?.parse().ok()?, &c.currency),
        _ => as_minor_units(c.amount.as_deref()?, &c.currency),
    }
}

#[derive(uniffi::Record)]
pub struct S5Report { pub checked: u32, pub failures: Vec<String> }

#[uniffi::export]
pub fn s5_rust_run_fixtures(json: String) -> S5Report {
    let f: Fixtures = match serde_json::from_str(&json) {
        Ok(f) => f,
        Err(e) => return S5Report { checked: 0, failures: vec![format!("fixture parse: {e}")] },
    };
    let mut failures = Vec::new();
    for c in &f.money {
        let got = money_result(c);
        if got != c.expect {
            failures.push(format!("money {} {:?} {:?} {}: got {got:?} want {:?}", c.op, c.amount, c.minor, c.currency, c.expect));
        }
    }
    for (i, c) in f.fingerprint.iter().enumerate() {
        if fingerprint(&c.segments) != c.expect {
            failures.push(format!("fingerprint #{i}"));
        }
    }
    for (i, c) in f.ranking.iter().enumerate() {
        if best_checked_deal(&c.groups) != c.best || lowest_advertised(&c.groups) != c.lowest {
            failures.push(format!("ranking #{i}"));
        }
    }
    let checked = (f.money.len() + f.fingerprint.len() + f.ranking.len()) as u32;
    S5Report { checked, failures }
}

/// Seconds spent running every fixture case `rounds` times (JSON decoding excluded).
#[uniffi::export]
pub fn s5_rust_bench(json: String, rounds: u32) -> f64 {
    let Ok(f) = serde_json::from_str::<Fixtures>(&json) else { return -1.0 };
    let start = Instant::now();
    let mut sink = 0usize;
    for _ in 0..rounds {
        for c in &f.money { sink += money_result(c).map_or(0, |s| s.len()); }
        for c in &f.fingerprint { sink += fingerprint(&c.segments).len(); }
        for c in &f.ranking { sink += best_checked_deal(&c.groups).len() + lowest_advertised(&c.groups).len(); }
    }
    std::hint::black_box(sink);
    start.elapsed().as_secs_f64()
}

#[cfg(test)]
mod tests {
    #[test]
    fn fixtures_match_python() {
        let json = std::fs::read_to_string(concat!(env!("CARGO_MANIFEST_DIR"), "/../fixtures.json")).unwrap();
        let report = super::s5_rust_run_fixtures(json);
        assert!(report.failures.is_empty(), "{} failures, first: {:?}", report.failures.len(), report.failures.first());
        assert_eq!(report.checked, 3806);
    }

    #[test]
    fn bench_prints_host_timing() {
        let json = std::fs::read_to_string(concat!(env!("CARGO_MANIFEST_DIR"), "/../fixtures.json")).unwrap();
        println!("Rust bench: 20 rounds in {:.3} s", super::s5_rust_bench(json, 20));
    }
}
