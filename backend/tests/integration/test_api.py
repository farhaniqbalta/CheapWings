import asyncio
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from test_worker import drain

from cheapwings.api.routes import create_app
from cheapwings.application import contracts as dto
from cheapwings.application.job_runner import JobRunner
from cheapwings.config import Settings
from cheapwings.domain.coverage import WorkStatus
from cheapwings.domain.offer import ProviderErrorCode
from cheapwings.providers.fake import FakeProvider, ScriptedOutcome
from cheapwings.providers.registry import Registration


def request_data():
    return {
        "origins": ["MEL"],
        "destinations": ["CGK", "DPS", "SUB"],
        "departure_date_from": "2026-12-12",
        "departure_date_through": "2026-12-20",
        "display_currency": "IDR",
    }


def client_for(engine, registry=None, settings=None):
    app = create_app(settings or Settings(), registry, engine)
    return TestClient(app, base_url="http://localhost", client=("127.0.0.1", 50000))


def test_api_scheduler_results_contract(engine):
    p = FakeProvider()
    p.script(
        "MEL",
        "DPS",
        "2026-12-12",
        ScriptedOutcome(WorkStatus.FAILED_TERMINAL, ProviderErrorCode.AUTH_DENIED),
    )
    reg = [Registration(p, minimum_interval_seconds=0)]
    with client_for(engine, reg) as client:
        assert client.get("/api/v1/health").json()["status"] == "ok"
        assert client.get("/api/v1/capabilities").json()["synthetic_mode"] is True
        response = client.post("/api/v1/searches", json=request_data())
        assert response.status_code == 202
        created = dto.Created.model_validate_json(response.text)
        job_id = created.job_id
        assert created.total_route_date_combinations == 27
        repo = client.app.state.repository
        asyncio.run(drain(JobRunner(repo, reg), repo, job_id))
        status = client.get(response.headers["location"])
        job = dto.Job.model_validate_json(status.text)
        assert job.status == "partial"
        assert job.covered_route_date_combinations == 26
        assert job.failed_provider_work_items == 1
        response = client.get(f"/api/v1/searches/{job_id}/results?limit=3")
        results = dto.Results.model_validate_json(response.text)
        assert len(results.itineraries) == 3
        assert results.next_cursor is not None
        seen = {i.itinerary_id for i in results.itineraries}
        as_of = results.as_of
        while results.next_cursor:
            response = client.get(
                f"/api/v1/searches/{job_id}/results",
                params={"cursor": results.next_cursor, "limit": 3},
            )
            results = dto.Results.model_validate_json(response.text)
            assert results.as_of == as_of
            assert not seen.intersection(i.itinerary_id for i in results.itineraries)
            seen.update(i.itinerary_id for i in results.itineraries)
        assert len(seen) == 26
        text = client.get(f"/api/v1/searches/{job_id}/results").text
        assert "fake-handle" not in text and "provider_quote_handle" not in text
        for itin in json.loads(text)["itineraries"]:
            for offer in itin["offers"]:
                assert isinstance(offer["amount_original"], str)
                assert isinstance(offer["comparable_amount"], str)
                assert "SYNTHETIC" in offer["seller"]
        assert client.get(f"/api/v1/searches/{job_id}/results?cursor=oops").status_code == 422
        assert client.post("/api/v1/searches/missing/cancel").status_code == 404


@pytest.mark.parametrize(
    "patch",
    [
        {"departure_date_from": "2020-01-01"},
        {"origins": ["BADCODE"]},
        {"departure_date_through": "2026-12-01"},
        {"passengers": {"adults": 2}},
        {"max_combinations": 9999},
        {"display_currency": "ZZZ"},
        {"max_stops": 9},
        {"origins": ["MEL"], "destinations": ["MEL"]},
    ],
)
def test_invalid_input_no_job(engine, patch):
    with client_for(engine) as c:
        response = c.post("/api/v1/searches", json=dict(request_data(), **patch))
        assert response.status_code == 422


def test_auth_and_remote_boundary(engine):
    token = "t" * 32
    with client_for(engine, settings=Settings(owner_token=token, bind_host="0.0.0.0")) as c:
        assert c.post("/api/v1/searches", json=request_data()).status_code == 401
        headers = {"Authorization": f"Bearer {token}"}
        response = c.post("/api/v1/searches", json=request_data(), headers=headers)
        assert response.status_code == 202
        job_id = response.json()["job_id"]
        assert c.get(f"/api/v1/searches/{job_id}").status_code == 401
        assert c.post(f"/api/v1/searches/{job_id}/cancel").status_code == 401
        assert (
            c.post(f"/api/v1/searches/{job_id}/cancel", headers=headers).json()["status"]
            == "cancelled"
        )
    with pytest.raises(ValueError):
        Settings(bind_host="0.0.0.0")
    app = create_app(Settings(), engine=engine)
    with TestClient(app, base_url="http://localhost", client=("10.0.0.1", 50000)) as c:
        assert c.get("/api/v1/health").status_code == 403
    with client_for(engine) as c:
        assert c.get("/api/v1/health", headers={"host": "evil.example"}).status_code == 403


def test_quota_and_cancel(engine):
    with client_for(engine, settings=Settings(max_active_jobs=1, max_hourly_jobs=1)) as c:
        first = c.post("/api/v1/searches", json=request_data()).json()
        assert c.post("/api/v1/searches", json=request_data()).status_code == 429
        url = first["job_status_url"]
        for _ in range(2):
            cancelled = c.post(url + "/cancel").json()
            assert cancelled["status"] == "cancelled"
            assert cancelled["cancelled_provider_work_items"] == 27
        assert c.post("/api/v1/searches", json=request_data()).status_code == 429


def test_openapi_committed_and_response_shapes(engine):
    with client_for(engine) as c:
        schema = c.get("/api/v1/openapi.json").json()
        assert schema == json.loads(
            (Path(__file__).parents[3] / "contracts/openapi.yaml").read_text()
        )
        assert (
            schema["components"]["schemas"]["PublicOffer"]["properties"]["amount_original"]["type"]
            == "string"
        )
        assert "provider_quote_handle" not in json.dumps(schema)
        assert schema["paths"]["/api/v1/searches"]["post"]["security"] == [{"HTTPBearer": []}]


def test_baggage_eligibility_and_snapshot_cursor(engine):
    reg = [Registration(FakeProvider(), minimum_interval_seconds=0)]
    with client_for(engine, reg) as c:
        response = c.post("/api/v1/searches", json=dict(request_data(), checked_bags_required=True))
        job_id = response.json()["job_id"]
        repo = c.app.state.repository
        asyncio.run(drain(JobRunner(repo, reg), repo, job_id))
        payload = c.get(f"/api/v1/searches/{job_id}/results").json()
        for group in payload["itineraries"]:
            ranked = next(o for o in group["offers"] if o["quote_id"] == group["ranked_quote_id"])
            assert ranked["checked_bag"] == "yes"
            assert any(
                o["comparison_status"] == "missing_required_baggage" for o in group["offers"]
            )


def test_safe_external_link_policy():
    from dataclasses import replace
    from datetime import date

    from cheapwings.application.search_service import public_offer
    from cheapwings.providers.base import SingleDateRouteQuery

    async def sample():
        return await FakeProvider().search(
            SingleDateRouteQuery("MEL", "DPS", date(2026, 12, 12), True, False, "IDR")
        )

    offer = asyncio.run(sample()).offers_by_itinerary_index[0][0]
    for link in ("javascript:alert(1)", "https://[broken", "https://user:pass@host/path"):
        projected = public_offer(replace(offer, link=link), 1)
        assert projected.link is None
        assert projected.link_scope == "unavailable"


async def test_pagination_freezes_incremental_quote_set(engine, query):
    from cheapwings.application.search_service import results_projection
    from cheapwings.storage.repository import Repository

    q = query.model_copy(update={"departure_date_through": query.departure_date_from})
    reg = [Registration(FakeProvider(), minimum_interval_seconds=0)]
    repo = Repository(engine, global_capacity=2)
    job = repo.create_job(q, reg)
    runner = JobRunner(repo, reg)
    await runner.tick()
    await asyncio.gather(*runner.tasks)
    first = results_projection(repo, job.id, "best_checked", limit=1)
    assert first.next_cursor is not None
    await drain(runner, repo, job.id)
    second = results_projection(repo, job.id, "best_checked", cursor=first.next_cursor, limit=1)
    assert second.next_cursor is None
    assert second.as_of == first.as_of
    assert second.itineraries[0].itinerary_id != first.itineraries[0].itinerary_id
    fresh = results_projection(repo, job.id, "best_checked")
    assert len(fresh.itineraries) == 3


def test_capabilities_report_default_source_selection(engine):
    registry = [Registration(FakeProvider(pid)) for pid in ("skiplagged", "swoop")]
    with client_for(engine, registry) as client:
        rows = client.get("/api/v1/capabilities").json()["providers"]
    # swoop stays enabled and selectable; it is only unchecked by default.
    assert {r["provider_id"]: (r["enabled"], r["default_selected"]) for r in rows} == {
        "skiplagged": (True, True),
        "swoop": (True, False),
    }
    with client_for(engine, registry, Settings(default_deselected_providers=())) as client:
        assert all(
            r["default_selected"] for r in client.get("/api/v1/capabilities").json()["providers"]
        )


def test_worker_pool_status_counts_shared_once_and_flags_cooldown(engine, query):
    from cheapwings.storage.repository import Repository

    fast = Registration(FakeProvider("fast"), minimum_interval_seconds=1)
    slow = Registration(FakeProvider("slow"), minimum_interval_seconds=1, priority=1)
    repo = Repository(engine, cache_enabled=True)
    q = query.model_copy(update={"destinations": ["DPS"]})
    first = repo.create_job(q, [fast, slow])
    second = repo.create_job(q, [fast, slow])  # same query: a shared in-flight operation
    assert repo.claim(fast) is not None and repo.claim(slow) is not None
    ops = [
        i.operation_id
        for j in (first, second)
        for i in repo.get_job(j.id)[1]
        if i.provider_id == "fast"
    ]
    # Every route-date fetch has two subscribers but is one physical operation.
    assert None not in ops and len(ops) == 2 * len(set(ops))
    repo.record_provider_feedback("slow", "http_rate_limited", 120)
    settings = Settings(worker_max_in_flight=16, low_priority_headroom=2)
    with client_for(engine, [fast, slow], settings) as client:
        pool = client.get("/api/v1/worker/pool").json()
    assert (pool["global_capacity"], pool["low_priority_headroom"], pool["running"]) == (16, 2, 2)
    rows = {p["provider_id"]: p for p in pool["providers"]}
    assert [p["provider_id"] for p in pool["providers"]] == ["fast", "slow"]  # by priority
    assert rows["fast"]["running"] == 1 and rows["slow"]["running"] == 1
    assert 0 < rows["fast"]["wait_ms"] <= 1000 and not rows["fast"]["cooling_down"]
    assert rows["slow"]["wait_ms"] > 100_000 and rows["slow"]["cooling_down"]
