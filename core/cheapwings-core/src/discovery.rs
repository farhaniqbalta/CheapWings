//! Discover (P7): provider-neutral price observations → a capped, explicit route/date shortlist.
//! Search keeps `planning::plan_search`; this module never expands a Cartesian product.

use crate::money::{fx_convert, parse};
use crate::planning::{normalize, parse_date, PlanError};
use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};
use std::fmt;

/// One priced destination lead from a discovery source. Unpriced rows never reach Rust.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DiscoveryObservation {
    pub origin: String,
    pub destination: String,
    /// `YYYY-MM-DD`
    pub departure_date: Option<String>,
    /// Decimal text, as provided.
    pub amount: String,
    pub currency: String,
    pub source_id: String,
    pub observed_at: Option<String>,
    pub fetched_at: String,
    /// historical | cached | indicative | unknown
    pub price_kind: String,
    /// yes | no | unknown (ThreeValued values, as on `RankOffer`/`SourceOffer`)
    pub hidden_city: String,
    pub source_reference: Option<String>,
}

/// 1 `currency` = `rate` display currency.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FxRate {
    pub currency: String,
    pub rate: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DiscoveryQuery {
    pub origins: Vec<String>,
    pub date_from: String,
    pub date_through: String,
    pub display_currency: String,
    /// In `display_currency`.
    pub budget: Option<String>,
    /// Same meaning and default (false) as Search's `include_hidden_city`.
    #[serde(default)]
    pub include_hidden_city: bool,
}

/// Flat on purpose: matches the fixture's `expect.selected` shape.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SelectedLead {
    pub origin: String,
    pub destination: String,
    pub date: String,
    pub observation_index: u32,
    pub comparable_amount: String,
}

#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct DiscoveryCounts {
    pub observed: u32,
    pub selected: u32,
    pub invalid: u32,
    pub hidden_city: u32,
    pub out_of_window: u32,
    pub undated: u32,
    pub no_fx: u32,
    pub over_budget: u32,
    pub superseded: u32,
    pub capped: u32,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DiscoveryPlan {
    pub selected: Vec<SelectedLead>,
    pub counts: DiscoveryCounts,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DiscoveryError {
    Plan(PlanError),
    InvalidCurrency(String),
    InvalidBudget(String),
}

impl DiscoveryError {
    pub fn code(&self) -> &'static str {
        match self {
            Self::Plan(e) => e.code(),
            Self::InvalidCurrency(_) => "invalid_currency",
            Self::InvalidBudget(_) => "invalid_budget",
        }
    }
}

impl fmt::Display for DiscoveryError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Plan(e) => e.fmt(f),
            Self::InvalidCurrency(c) => write!(f, "unsupported display currency {c:?}"),
            Self::InvalidBudget(b) => {
                write!(f, "invalid budget {b:?}; expected a positive decimal")
            }
        }
    }
}

impl std::error::Error for DiscoveryError {}

impl From<PlanError> for DiscoveryError {
    fn from(e: PlanError) -> Self {
        Self::Plan(e)
    }
}

/// Discovery may shortlist near-budget leads; only detailed fares are "checked within budget".
const BUDGET_HEADROOM: Decimal = Decimal::from_parts(110, 0, 0, false, 2);

struct Survivor {
    index: u32,
    origin: String,
    destination: String,
    day: i64,
    date: String,
    comparable: Decimal,
    comparable_text: String,
}

fn code(text: &str) -> String {
    crate::python_strip(text).to_uppercase()
}

/// Cheapest priced lead per destination inside the query window, capped at `max_route_dates`.
/// The caller derives the cap from its work-item limit and enabled providers.
pub fn select_discovery_plan(
    observations: &[DiscoveryObservation],
    query: &DiscoveryQuery,
    fx: &[FxRate],
    max_route_dates: u32,
) -> Result<DiscoveryPlan, DiscoveryError> {
    let origins = normalize(&query.origins)?;
    let (from, through) = (
        parse_date(&query.date_from)?,
        parse_date(&query.date_through)?,
    );
    if through < from {
        return Err(PlanError::DatesReversed.into());
    }
    let display = code(&query.display_currency);
    fx_convert("0", "1", &display)
        .map_err(|_| DiscoveryError::InvalidCurrency(query.display_currency.clone()))?;
    let ceiling = match &query.budget {
        None => None,
        Some(b) => {
            let budget = parse(b)
                .ok()
                .filter(|d| *d > Decimal::ZERO)
                .ok_or_else(|| DiscoveryError::InvalidBudget(b.clone()))?;
            Some(
                budget
                    .checked_mul(BUDGET_HEADROOM)
                    .ok_or_else(|| DiscoveryError::InvalidBudget(b.clone()))?,
            )
        }
    };

    let mut counts = DiscoveryCounts {
        observed: observations.len() as u32,
        ..Default::default()
    };
    let mut survivors: Vec<Survivor> = Vec::new();
    for (index, obs) in observations.iter().enumerate() {
        let route = normalize(&[obs.origin.clone(), obs.destination.clone()]);
        let date = obs.departure_date.as_deref().map(parse_date).transpose();
        let positive = parse(&obs.amount).is_ok_and(|a| a > Decimal::ZERO);
        let (route, day) = match (route, date) {
            (Ok(r), Ok(day)) if r.len() == 2 && origins.contains(&r[0]) && positive => (r, day),
            _ => {
                counts.invalid += 1;
                continue;
            }
        };
        if obs.hidden_city == "yes" && !query.include_hidden_city {
            counts.hidden_city += 1;
            continue;
        }
        let Some(day) = day else {
            counts.undated += 1;
            continue;
        };
        if day < from || day > through {
            counts.out_of_window += 1;
            continue;
        }
        let currency = code(&obs.currency);
        let rate = if currency == display {
            Some("1")
        } else {
            fx.iter()
                .find(|r| code(&r.currency) == currency)
                .map(|r| r.rate.as_str())
        };
        let Some(comparable_text) = rate.and_then(|r| fx_convert(&obs.amount, r, &display).ok())
        else {
            counts.no_fx += 1;
            continue;
        };
        let comparable = parse(&comparable_text).expect("fx_convert returns a decimal");
        if ceiling.is_some_and(|c| comparable > c) {
            counts.over_budget += 1;
            continue;
        }
        let [origin, destination]: [String; 2] = route.try_into().expect("two codes");
        survivors.push(Survivor {
            index: index as u32,
            origin,
            destination,
            day,
            date: obs.departure_date.clone().expect("dated"),
            comparable,
            comparable_text,
        });
    }

    // One winner per destination: cheapest, then earlier date, origin, index.
    survivors.sort_by(|a, b| {
        (&a.destination, a.comparable, a.day, &a.origin, a.index).cmp(&(
            &b.destination,
            b.comparable,
            b.day,
            &b.origin,
            b.index,
        ))
    });
    let before = survivors.len();
    survivors.dedup_by(|later, first| later.destination == first.destination);
    counts.superseded = (before - survivors.len()) as u32;
    survivors.sort_by(|a, b| (a.comparable, &a.destination).cmp(&(b.comparable, &b.destination)));
    let keep = survivors.len().min(max_route_dates as usize);
    counts.capped = (survivors.len() - keep) as u32;
    counts.selected = keep as u32;
    let selected = survivors
        .into_iter()
        .take(keep)
        .map(|s| SelectedLead {
            origin: s.origin,
            destination: s.destination,
            date: s.date,
            observation_index: s.index,
            comparable_amount: s.comparable_text,
        })
        .collect();
    Ok(DiscoveryPlan { selected, counts })
}
