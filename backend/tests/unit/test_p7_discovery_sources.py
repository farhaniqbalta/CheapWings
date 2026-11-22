"""P7.4 discovery sources through PyO3: same fixture as Rust and Swift."""

import json
from pathlib import Path

import cheapwings_core as core
import pytest

FIXTURE = Path(__file__).resolve().parents[3] / "contracts" / "fixtures" / "core" / "discovery_sources_fixtures.json"
DATA = json.loads(FIXTURE.read_text())


@pytest.mark.parametrize("case", DATA["anywhere"], ids=[c["name"] for c in DATA["anywhere"]])
def test_anywhere_case(case):
    payload = json.dumps({k: case[k] for k in ("rpc_json", "origin", "depart", "fetched_at")})
    expect = case["expect"]
    if "error" in expect:
        with pytest.raises(ValueError, match=f"^{expect['error']}:"):
            core.skiplagged_anywhere(payload)
        return
    page = json.loads(core.skiplagged_anywhere(payload))
    if "observations" in expect:
        assert page["observations"] == expect["observations"]
    if "count" in expect:
        assert len(page["observations"]) == expect["count"]
        assert (page["observations"] or [None])[0] == expect["first"]
    assert page["unpriced"] == expect["unpriced"]
    assert page["fx"] == expect["fx"]


@pytest.mark.parametrize("case", DATA["discovery_calls"], ids=[c["name"] for c in DATA["discovery_calls"]])
def test_discovery_calls_case(case):
    expect = case["expect"]
    if "error" in expect:
        with pytest.raises(ValueError, match=f"^{expect['error']}:"):
            core.discovery_calls(json.dumps(case["query"]))
        return
    calls = json.loads(core.discovery_calls(json.dumps(case["query"])))
    if "calls" in expect:
        assert calls == expect["calls"]
    else:
        assert len(calls) == expect["count"]
