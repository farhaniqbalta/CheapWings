//! Route × date planning, behaviour-compatible with `SearchQuery` validation
//! (`backend/src/cheapwings/domain/query.py`) and `expand_routes_and_dates`
//! (`engine/expansion.py`): order origin → destination → date, same-airport pairs skipped.

use serde::Deserialize;
use std::fmt;

#[derive(Debug, Clone, PartialEq, Eq, Deserialize)]
pub struct RouteDate {
    pub origin: String,
    pub destination: String,
    /// `YYYY-MM-DD`
    pub date: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PlanError {
    InvalidAirport(String),
    NoAirports,
    DatesReversed,
    InvalidDate(String),
    SameAirport(String),
    TooMany { combinations: u32, max: u32 },
}

impl PlanError {
    pub fn code(&self) -> &'static str {
        match self {
            Self::InvalidAirport(_) => "invalid_airport",
            Self::NoAirports => "no_airports",
            Self::DatesReversed => "dates_reversed",
            Self::InvalidDate(_) => "invalid_date",
            Self::SameAirport(_) => "same_airport",
            Self::TooMany { .. } => "too_many",
        }
    }
}

impl fmt::Display for PlanError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InvalidAirport(code) => write!(f, "invalid IATA code {code:?}"),
            Self::NoAirports => write!(f, "at least one airport code is required"),
            Self::DatesReversed => write!(f, "end date is before start date"),
            Self::InvalidDate(text) => write!(f, "invalid date {text:?}; expected YYYY-MM-DD"),
            Self::SameAirport(code) => write!(f, "origin and destination cannot both be {code}"),
            Self::TooMany { combinations, max } => {
                write!(f, "{combinations} combinations exceeds the maximum of {max}; narrow the airports or dates")
            }
        }
    }
}

impl std::error::Error for PlanError {}

/// Trim, uppercase, require `^[A-Z]{3}$`, de-duplicate keeping first occurrence.
fn normalize(codes: &[String]) -> Result<Vec<String>, PlanError> {
    if codes.is_empty() {
        return Err(PlanError::NoAirports);
    }
    let mut out: Vec<String> = Vec::new();
    for code in codes {
        let upper = code.trim().to_uppercase();
        if upper.len() != 3 || !upper.bytes().all(|b| b.is_ascii_uppercase()) {
            return Err(PlanError::InvalidAirport(code.clone()));
        }
        if !out.contains(&upper) {
            out.push(upper);
        }
    }
    Ok(out)
}

/// Days since 1970-01-01 for a proleptic Gregorian date (Howard Hinnant's algorithm).
fn days_from_civil(y: i64, m: i64, d: i64) -> i64 {
    let y = if m <= 2 { y - 1 } else { y };
    let era = y.div_euclid(400);
    let yoe = y - era * 400;
    let doy = (153 * (m + if m > 2 { -3 } else { 9 }) + 2) / 5 + d - 1;
    let doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    era * 146_097 + doe - 719_468
}

fn civil_from_days(z: i64) -> (i64, i64, i64) {
    let z = z + 719_468;
    let era = z.div_euclid(146_097);
    let doe = z - era * 146_097;
    let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = doy - (153 * mp + 2) / 5 + 1;
    let m = if mp < 10 { mp + 3 } else { mp - 9 };
    (yoe + era * 400 + i64::from(m <= 2), m, d)
}

/// Strict `YYYY-MM-DD` → day number; rejects impossible dates (e.g. 2027-02-29).
fn parse_date(text: &str) -> Result<i64, PlanError> {
    let invalid = || PlanError::InvalidDate(text.to_owned());
    let bytes = text.as_bytes();
    if bytes.len() != 10 || bytes[4] != b'-' || bytes[7] != b'-' {
        return Err(invalid());
    }
    let num = |range: std::ops::Range<usize>| text.get(range).filter(|s| s.bytes().all(|b| b.is_ascii_digit())).and_then(|s| s.parse::<i64>().ok());
    let (y, m, d) = (num(0..4).ok_or_else(invalid)?, num(5..7).ok_or_else(invalid)?, num(8..10).ok_or_else(invalid)?);
    let day = days_from_civil(y, m, d);
    if !(1..=12).contains(&m) || civil_from_days(day) != (y, m, d) {
        return Err(invalid());
    }
    Ok(day)
}

fn format_date(day: i64) -> String {
    let (y, m, d) = civil_from_days(day);
    format!("{y:04}-{m:02}-{d:02}")
}

pub fn plan_search(
    origins: &[String],
    destinations: &[String],
    date_from: &str,
    date_through: &str,
    max_combinations: u32,
) -> Result<Vec<RouteDate>, PlanError> {
    let origins = normalize(origins)?;
    let destinations = normalize(destinations)?;
    let (start, end) = (parse_date(date_from)?, parse_date(date_through)?);
    if end < start {
        return Err(PlanError::DatesReversed);
    }
    if origins.len() == 1 && destinations == origins {
        return Err(PlanError::SameAirport(origins[0].clone()));
    }
    let pairs: Vec<(&String, &String)> = origins
        .iter()
        .flat_map(|o| destinations.iter().map(move |d| (o, d)))
        .filter(|(o, d)| o != d)
        .collect();
    let days = end - start + 1;
    let combinations = u32::try_from(pairs.len() as i64 * days).unwrap_or(u32::MAX);
    if combinations > max_combinations {
        return Err(PlanError::TooMany { combinations, max: max_combinations });
    }
    Ok(pairs
        .into_iter()
        .flat_map(|(o, d)| {
            (start..=end).map(move |day| RouteDate { origin: o.clone(), destination: d.clone(), date: format_date(day) })
        })
        .collect())
}
