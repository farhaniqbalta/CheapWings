//! Thin PyO3 wrappers over the `cheapwings-core` crate. Values cross as text; every error
//! is a `ValueError`; host adapters preserve their public validation and result types.

use engine::money::{self, MoneyError};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

fn to_py(err: MoneyError) -> PyErr {
    PyValueError::new_err(err.to_string())
}

#[pyfunction]
fn minor_unit_exponent(currency: &str) -> PyResult<u32> {
    money::minor_unit_exponent(currency).map_err(to_py)
}

#[pyfunction]
fn from_minor_units(minor: i128, currency: &str) -> PyResult<String> {
    money::from_minor_units(minor, currency).map_err(to_py)
}

#[pyfunction]
fn as_minor_units(amount: &str, currency: &str) -> PyResult<i128> {
    money::as_minor_units(amount, currency).map_err(to_py)
}

#[pyfunction]
fn fx_convert(amount: &str, rate: &str, quote_currency: &str) -> PyResult<String> {
    money::fx_convert(amount, rate, quote_currency).map_err(to_py)
}

#[pyfunction]
fn fold(value: &str) -> String {
    engine::locations::fold(value)
}

type Instant = (i32, u32, u32, u32, u32, u32, u32, i64);
type Segment = (
    i64,
    String,
    String,
    String,
    String,
    String,
    Instant,
    Instant,
);

#[pyfunction]
fn fingerprint(segments: Vec<Segment>) -> String {
    use engine::fingerprint::{LocalInstant, Segment};
    let instant = |(y, mo, d, h, mi, s, us, offset): Instant| LocalInstant {
        y,
        mo,
        d,
        h,
        mi,
        s,
        us,
        offset: (offset / 1_000_000) as i32,
        offset_fraction: (offset % 1_000_000) as i32,
    };
    let segments = segments
        .into_iter()
        .map(
            |(ordinal, marketing, operating, flight, origin, destination, depart, arrive)| {
                Segment {
                    ordinal,
                    marketing,
                    operating,
                    flight,
                    origin,
                    destination,
                    depart: instant(depart),
                    arrive: instant(arrive),
                }
            },
        )
        .collect::<Vec<_>>();
    engine::fingerprint::fingerprint(&segments)
}

#[pyfunction]
fn rank_offers(
    offers: Vec<(String, String, String, Option<String>)>,
    best: bool,
) -> PyResult<Vec<usize>> {
    for (_, _, _, amount) in &offers {
        if let Some(amount) = amount {
            engine::ranking::validate_amount(amount).map_err(PyValueError::new_err)?;
        }
    }
    let groups = vec![offers
        .into_iter()
        .enumerate()
        .map(
            |(i, (price_status, hidden_city, comparison_status, amount))| {
                engine::ranking::RankOffer {
                    id: i.to_string(),
                    price_status,
                    hidden_city,
                    comparison_status,
                    amount,
                }
            },
        )
        .collect()];
    let ids = if best {
        engine::ranking::best_checked_deal(&groups)
    } else {
        engine::ranking::lowest_advertised(&groups)
    };
    Ok(ids
        .iter()
        .map(|id| id.parse().expect("input position"))
        .collect())
}

#[pyfunction]
fn plan_search(
    origins: Vec<String>,
    destinations: Vec<String>,
    start: &str,
    end: &str,
    max_combinations: u32,
) -> PyResult<Vec<(String, String, String)>> {
    engine::planning::plan_search(&origins, &destinations, start, end, max_combinations)
        .map(|routes| {
            routes
                .into_iter()
                .map(|r| (r.origin, r.destination, r.date))
                .collect()
        })
        .map_err(|e| PyValueError::new_err(e.to_string()))
}

#[pyfunction]
fn plan_scope(
    origins: Vec<String>,
    destinations: Vec<String>,
    start: &str,
    end: &str,
    providers: Vec<String>,
) -> PyResult<(u64, u64, u64, u64, u64)> {
    engine::planning::scope(&origins, &destinations, start, end, &providers)
        .map_err(|e| PyValueError::new_err(e.to_string()))
}

fn catalog_error(error: engine::locations::CatalogError) -> PyErr {
    use engine::locations::CatalogError::*;
    let message = match error {
        TooLong => "Search text exceeds 100 characters".to_owned(),
        UnknownLocation(_) => "Unknown location ID; reload the catalog".to_owned(),
        StaleVersion => "Stale catalog version; reload and review the included airports".to_owned(),
        TypeMismatch => "Unknown location ID or mismatched location type".to_owned(),
        NoMajorMapping => "No curated major-airport mapping; use Specific Airports".to_owned(),
        DuplicateLocation => "Duplicate location ID".to_owned(),
        DuplicateAirport => "Duplicate airport code".to_owned(),
        AirportWithoutCode => "Invalid location catalog: airport without code".to_owned(),
        InvalidAssociation => "Invalid airport association".to_owned(),
        InvalidMappingId => "Invalid mapping ID".to_owned(),
        InvalidMapping => "Invalid major mapping".to_owned(),
        Invalid(why) => format!("Invalid location catalog: {why}"),
    };
    PyValueError::new_err(message)
}

#[pyclass(name = "LocationCatalog")]
struct LocationCatalog {
    catalog: engine::locations::Catalog,
}

#[pymethods]
impl LocationCatalog {
    #[new]
    fn new(text: &str) -> PyResult<Self> {
        Ok(Self {
            catalog: engine::locations::Catalog::from_json(text).map_err(catalog_error)?,
        })
    }

    #[pyo3(signature = (text, within=None))]
    fn search(&self, text: &str, within: Option<&str>) -> PyResult<Vec<String>> {
        self.catalog
            .search(text, within)
            .map(|items| items.into_iter().map(|i| i.id).collect())
            .map_err(catalog_error)
    }

    fn airports_of(&self, id: &str) -> PyResult<Vec<String>> {
        self.catalog
            .airports_of(id)
            .map(|items| items.into_iter().map(|i| i.id).collect())
            .map_err(catalog_error)
    }

    fn resolve(
        &self,
        kind: &str,
        id: &str,
        version: &str,
    ) -> PyResult<(Vec<String>, String, String)> {
        self.catalog
            .resolve_major(kind, id, version)
            .map(|r| (r.codes, r.rationale, r.definition))
            .map_err(|e| {
                // Major resolution historically combines unknown IDs and type mismatch.
                if matches!(e, engine::locations::CatalogError::UnknownLocation(_)) {
                    catalog_error(engine::locations::CatalogError::TypeMismatch)
                } else {
                    catalog_error(e)
                }
            })
    }
}

#[pyfunction]
fn skiplagged_parse(
    payload: &str,
    origin: &str,
    destination: &str,
    date: &str,
) -> PyResult<String> {
    engine::skiplagged::web_payload(payload, origin, destination, date)
        .map_err(|error| PyValueError::new_err(error.code()))
}

#[pyfunction]
fn select_discovery_plan(payload: &str) -> PyResult<String> {
    engine::discovery::web_payload(payload).map_err(PyValueError::new_err)
}

#[pyfunction]
fn discovery_calls(payload: &str) -> PyResult<String> {
    engine::discovery_sources::calls_web_payload(payload).map_err(PyValueError::new_err)
}

#[pyfunction]
fn skiplagged_anywhere(payload: &str) -> PyResult<String> {
    engine::discovery_sources::anywhere_web_payload(payload).map_err(PyValueError::new_err)
}

#[pyfunction]
fn fli_parse(payload: &str) -> PyResult<String> {
    engine::fli::web_payload(payload).map_err(|error| PyValueError::new_err(error.code()))
}

#[pyfunction]
fn fli_extract_ds1(html: &str) -> PyResult<String> {
    engine::fli::extract_ds1(html)
        .map(|data| data.to_string())
        .ok_or_else(|| PyValueError::new_err("schema_changed"))
}

#[pymodule]
fn cheapwings_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("BUILD_REVISION", engine::BUILD_REVISION)?;
    m.add_function(wrap_pyfunction!(minor_unit_exponent, m)?)?;
    m.add_function(wrap_pyfunction!(select_discovery_plan, m)?)?;
    m.add_function(wrap_pyfunction!(discovery_calls, m)?)?;
    m.add_function(wrap_pyfunction!(skiplagged_anywhere, m)?)?;
    m.add_function(wrap_pyfunction!(from_minor_units, m)?)?;
    m.add_function(wrap_pyfunction!(as_minor_units, m)?)?;
    m.add_function(wrap_pyfunction!(fx_convert, m)?)?;
    m.add_function(wrap_pyfunction!(fold, m)?)?;
    m.add_function(wrap_pyfunction!(fingerprint, m)?)?;
    m.add_function(wrap_pyfunction!(rank_offers, m)?)?;
    m.add_function(wrap_pyfunction!(plan_search, m)?)?;
    m.add_function(wrap_pyfunction!(plan_scope, m)?)?;
    m.add_class::<LocationCatalog>()?;
    m.add_function(wrap_pyfunction!(fli_parse, m)?)?;
    m.add_function(wrap_pyfunction!(fli_extract_ds1, m)?)?;
    m.add_function(wrap_pyfunction!(skiplagged_parse, m)?)?;
    Ok(())
}
