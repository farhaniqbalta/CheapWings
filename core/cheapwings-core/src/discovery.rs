//! Discover (P7): provider-neutral price observations → a capped, explicit route/date shortlist.
//! Search keeps `planning::plan_search`; this module never expands a Cartesian product.

use crate::planning::PlanError;
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
            Self::InvalidBudget(b) => write!(f, "invalid budget {b:?}; expected a positive decimal"),
        }
    }
}

impl std::error::Error for DiscoveryError {}

impl From<PlanError> for DiscoveryError {
    fn from(e: PlanError) -> Self {
        Self::Plan(e)
    }
}
