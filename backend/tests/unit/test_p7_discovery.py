"""P7 Discover contract through PyO3: same fixture as Rust and Swift."""

import json
from pathlib import Path

import cheapwings_core as core
import pytest

FIXTURE = Path(__file__).resolve().parents[3] / "contracts" / "fixtures" / "core" / "discovery_fixtures.json"
CASES = json.loads(FIXTURE.read_text())["cases"]


def test_binding_exists():
    assert hasattr(core, "select_discovery_plan")


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_fixture_case(case):
    payload = json.dumps({k: case[k] for k in ("observations", "query", "fx", "max_route_dates")})
    if "error" in case["expect"]:
        with pytest.raises(ValueError, match=f"^{case['expect']['error']}:"):
            core.select_discovery_plan(payload)
    else:
        assert json.loads(core.select_discovery_plan(payload)) == case["expect"]


def test_bad_json_is_value_error():
    with pytest.raises(ValueError):
        core.select_discovery_plan("{not json")


def test_plan_search_unchanged():
    assert len(core.plan_search(["CGK"], ["DPS"], "2027-03-01", "2027-03-02", 120)) == 2
