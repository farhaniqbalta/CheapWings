//! Location catalog: typed search, browse a place's airports, authoritative Major-airport
//! resolution and airport lookup. Port of `backend/src/cheapwings/locations/catalog.py`;
//! the catalog JSON itself is shared unchanged with the backend and web app.

use serde::Deserialize;
use std::collections::{HashMap, HashSet};
use std::fmt;
use unicode_normalization::char::is_combining_mark;
use unicode_normalization::UnicodeNormalization;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Location {
    pub id: String,
    /// `airport | city | country`
    pub kind: String,
    pub name: String,
    pub code: Option<String>,
    pub city: Option<String>,
    pub country: String,
    pub country_name: String,
    pub codes: Vec<String>,
    pub timezone: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MajorResolution {
    pub codes: Vec<String>,
    pub rationale: String,
    pub definition: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CatalogError {
    Invalid(String),
    TooLong,
    UnknownLocation(String),
    StaleVersion,
    TypeMismatch,
    NoMajorMapping,
}

impl CatalogError {
    pub fn code(&self) -> &'static str {
        match self {
            Self::Invalid(_) => "invalid",
            Self::TooLong => "too_long",
            Self::UnknownLocation(_) => "unknown_location",
            Self::StaleVersion => "stale_version",
            Self::TypeMismatch => "type_mismatch",
            Self::NoMajorMapping => "no_major_mapping",
        }
    }
}

impl fmt::Display for CatalogError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Invalid(why) => write!(f, "invalid location catalog: {why}"),
            Self::TooLong => write!(f, "search text exceeds 100 characters"),
            Self::UnknownLocation(id) => write!(f, "unknown location {id:?}; reload the catalog"),
            Self::StaleVersion => write!(f, "stale catalog version; reload and review the included airports"),
            Self::TypeMismatch => write!(f, "location type does not match"),
            Self::NoMajorMapping => write!(f, "no curated major-airport list; use specific airports"),
        }
    }
}

impl std::error::Error for CatalogError {}

#[derive(Deserialize)]
struct RawEntity {
    id: String,
    #[serde(rename = "type")]
    kind: String,
    name: String,
    country: String,
    country_name: String,
    codes: Vec<String>,
    #[serde(default)]
    aliases: Vec<String>,
    code: Option<String>,
    city: Option<String>,
    timezone: Option<String>,
}

#[derive(Deserialize)]
struct RawMajor {
    codes: Vec<String>,
    rationale: String,
}

#[derive(Deserialize)]
struct RawCatalog {
    version: String,
    definition: String,
    entities: Vec<RawEntity>,
    major: HashMap<String, RawMajor>,
}

/// Python `fold`: NFKD, casefold, combining marks dropped.
pub fn fold(text: &str) -> String {
    text.nfkd()
        .flat_map(|c| match c {
            // Python casefold maps these to "ss"; Rust's to_lowercase keeps ß.
            'ß' | 'ẞ' => "ss".chars().collect::<Vec<_>>(),
            other => other.to_lowercase().collect(),
        })
        .filter(|c| !is_combining_mark(*c))
        .collect()
}

pub struct Catalog {
    version: String,
    definition: String,
    entities: Vec<Location>,
    aliases: Vec<Vec<String>>,
    by_id: HashMap<String, usize>,
    airports: HashMap<String, usize>,
    major: HashMap<String, RawMajor>,
    index: Vec<String>,
}

impl Catalog {
    /// Parses and validates the catalog exactly as `LocationCatalog.__init__` does; fails closed.
    pub fn from_json(text: &str) -> Result<Catalog, CatalogError> {
        let raw: RawCatalog = serde_json::from_str(text).map_err(|e| CatalogError::Invalid(e.to_string()))?;
        let invalid = |why: &str| CatalogError::Invalid(why.to_owned());
        let mut by_id = HashMap::new();
        let mut airports = HashMap::new();
        for (i, e) in raw.entities.iter().enumerate() {
            if by_id.insert(e.id.clone(), i).is_some() {
                return Err(invalid("duplicate location ID"));
            }
            if e.kind == "airport" {
                let code = e.code.clone().ok_or_else(|| invalid("airport without code"))?;
                if airports.insert(code, i).is_some() {
                    return Err(invalid("duplicate airport code"));
                }
            }
        }
        for e in &raw.entities {
            let unique: HashSet<&String> = e.codes.iter().collect();
            if unique.len() != e.codes.len() || !e.codes.iter().all(|c| airports.contains_key(c)) {
                return Err(invalid("invalid airport association"));
            }
        }
        for (id, mapping) in &raw.major {
            let entity = by_id.get(id).map(|&i| &raw.entities[i]).ok_or_else(|| invalid("invalid mapping ID"))?;
            if entity.kind == "airport" {
                return Err(invalid("invalid mapping ID"));
            }
            let unique: HashSet<&String> = mapping.codes.iter().collect();
            if mapping.codes.is_empty() || unique.len() != mapping.codes.len() || !mapping.codes.iter().all(|c| entity.codes.contains(c)) {
                return Err(invalid("invalid major mapping"));
            }
        }
        let index = raw
            .entities
            .iter()
            .map(|e| {
                let mut parts = vec![
                    e.name.clone(),
                    e.code.clone().unwrap_or_default(),
                    e.city.clone().unwrap_or_default(),
                    e.country_name.clone(),
                ];
                parts.extend(e.aliases.iter().cloned());
                fold(&parts.join(" "))
            })
            .collect();
        let aliases = raw.entities.iter().map(|e| e.aliases.clone()).collect();
        let entities = raw
            .entities
            .into_iter()
            .map(|e| Location {
                id: e.id,
                kind: e.kind,
                name: e.name,
                code: e.code,
                city: e.city,
                country: e.country,
                country_name: e.country_name,
                codes: e.codes,
                timezone: e.timezone,
            })
            .collect();
        Ok(Catalog { version: raw.version, definition: raw.definition, entities, aliases, by_id, airports, major: raw.major, index })
    }

    pub fn version(&self) -> &str {
        &self.version
    }

    /// Full deterministic matches (presentation may paginate; selection never truncates).
    /// `within` limits results to that place's airports; an empty term then lists them all.
    pub fn search(&self, text: &str, within: Option<&str>) -> Result<Vec<Location>, CatalogError> {
        if text.chars().count() > 100 {
            return Err(CatalogError::TooLong);
        }
        let term = fold(text.trim());
        let allowed: Option<HashSet<String>> = match within {
            None => None,
            Some(id) => Some(self.airports_of(id)?.into_iter().map(|l| l.id).collect()),
        };
        let mut matches: Vec<usize> = (0..self.entities.len())
            .filter(|&i| {
                let e = &self.entities[i];
                let in_scope = allowed.as_ref().map_or(true, |a| a.contains(&e.id));
                in_scope && ((!term.is_empty() && self.index[i].contains(&term)) || (allowed.is_some() && term.is_empty()))
            })
            .collect();
        matches.sort_by_cached_key(|&i| {
            let e = &self.entities[i];
            let exact_code = term != fold(e.code.as_deref().unwrap_or(""));
            let exact_name = !(term == fold(&e.name) || self.aliases[i].iter().any(|a| fold(a) == term));
            (exact_code, exact_name, e.kind.clone(), fold(&e.name), e.id.clone())
        });
        Ok(matches.into_iter().map(|i| self.entities[i].clone()).collect())
    }

    pub fn airports_of(&self, id: &str) -> Result<Vec<Location>, CatalogError> {
        let &i = self.by_id.get(id).ok_or_else(|| CatalogError::UnknownLocation(id.to_owned()))?;
        Ok(self.entities[i].codes.iter().map(|c| self.entities[self.airports[c]].clone()).collect())
    }

    pub fn has_major(&self, id: &str) -> bool {
        self.major.contains_key(id)
    }

    pub fn resolve_major(&self, kind: &str, id: &str, version: &str) -> Result<MajorResolution, CatalogError> {
        if version != self.version {
            return Err(CatalogError::StaleVersion);
        }
        let &i = self.by_id.get(id).ok_or_else(|| CatalogError::UnknownLocation(id.to_owned()))?;
        if self.entities[i].kind != kind {
            return Err(CatalogError::TypeMismatch);
        }
        let mapping = self.major.get(id).ok_or(CatalogError::NoMajorMapping)?;
        let mut codes = mapping.codes.clone();
        codes.sort();
        Ok(MajorResolution { codes, rationale: mapping.rationale.clone(), definition: self.definition.clone() })
    }

    pub fn airport(&self, code: &str) -> Option<Location> {
        self.airports.get(code).map(|&i| self.entities[i].clone())
    }
}
