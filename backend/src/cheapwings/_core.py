"""Load and validate the native extension once for all backend callers."""

from importlib import import_module

from cheapwings._core_revision import EXPECTED_REVISION

_REBUILD = "Run: maturin develop --release -m core/cheapwings-py/Cargo.toml"
_REQUIRED = (
    "fingerprint",
    "rank_offers",
    "plan_search",
    "plan_scope",
    "fold",
    "LocationCatalog",
    "minor_unit_exponent",
    "as_minor_units",
    "from_minor_units",
    "fx_convert",
    "BUILD_REVISION",
)


def _load():
    try:
        binding = import_module("cheapwings_core")
    except ImportError as exc:
        raise ImportError(f"Cannot load cheapwings_core. {_REBUILD}") from exc
    for name in _REQUIRED:
        if not hasattr(binding, name):
            raise ImportError(f"cheapwings_core missing export {name}. {_REBUILD}")
    if binding.BUILD_REVISION != EXPECTED_REVISION:
        raise ImportError(f"cheapwings_core revision mismatch. {_REBUILD}")
    return binding


core = _load()
