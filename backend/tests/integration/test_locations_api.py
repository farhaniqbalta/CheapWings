from datetime import date, timedelta

import pytest
from cheapwings.config import Settings
from cheapwings.locations.catalog import catalog
from cheapwings.providers.fake import FakeProvider
from cheapwings.providers.registry import Registration
from test_api import client_for


def major(id="metro:JP:TYO", type="city"):
    return {
        "type": type,
        "location_id": id,
        "coverage_mode": "major",
        "catalog_version": catalog().version,
    }


def body(**patch):
    start = date.today() + timedelta(days=10)
    return dict(
        origins=["CGK"],
        destinations=["HND", "NRT"],
        departure_date_from=start.isoformat(),
        departure_date_through=start.isoformat(),
        **patch,
    )


def test_resolve_submit_and_persist_authoritative_major_scope(engine):
    with client_for(engine, [Registration(FakeProvider())]) as c:
        resolution = c.post("/api/v1/locations/resolve", json=major())
        assert resolution.status_code == 200
        assert resolution.json()["codes"] == ["HND", "NRT"]
        assert resolution.json()["rationale"]
        response = c.post("/api/v1/searches", json=body(destination_selection=major()))
        assert response.status_code == 202
        assert response.json()["total_route_date_combinations"] == 2
        job = c.get(response.headers["location"]).json()
        assert job["query"]["destination_selection"] == major()
        assert job["query"]["destinations"] == ["HND", "NRT"]
        assert job["total_provider_work_items"] == 2


@pytest.mark.parametrize(
    "patch",
    [
        {"destination_selection": {**major(), "catalog_version": "stale"}},
        {"destination_selection": {**major(), "location_id": "missing"}},
        {"destination_selection": major("country:US", "country")},
        {"destination_selection": {**major(), "type": "country"}},
        {"destination_selection": {**major(), "coverage_mode": "all"}},
        {"destination_selection": {**major(), "location_id": "x" * 513}},
        {"destination_selection": {**major(), "arbitrary": True}},
    ],
)
def test_invalid_major_scope_never_creates_job(engine, patch):
    with client_for(engine, [Registration(FakeProvider())]) as c:
        assert c.post("/api/v1/searches", json=body(**patch)).status_code == 422


@pytest.mark.parametrize(
    "codes", [["HND"], ["HND", "NRT", "KIX"], ["TYO"], ["Japan"], ["A" * 100000]]
)
def test_major_arrays_cannot_be_truncated_expanded_or_metro_codes(engine, codes):
    payload = body(destination_selection=major())
    payload["destinations"] = codes
    with client_for(engine, [Registration(FakeProvider())]) as c:
        assert c.post("/api/v1/searches", json=payload).status_code == 422


def test_runtime_cap_and_overlap_legacy_arrays(engine):
    registry = [Registration(FakeProvider())]
    with client_for(engine, registry, Settings(max_combinations=2)) as c:
        assert c.get("/api/v1/capabilities").json()["max_route_date_combinations"] == 2
        payload = body()
        payload.update(
            origins=["CGK", "HND", "cgk"],
            destinations=["HND"],
            departure_date_through=(
                date.fromisoformat(payload["departure_date_from"]) + timedelta(days=1)
            ).isoformat(),
        )
        response = c.post("/api/v1/searches", json=payload)
        assert response.status_code == 202
        assert response.json()["total_route_date_combinations"] == 2
        payload["departure_date_through"] = (
            date.fromisoformat(payload["departure_date_from"]) + timedelta(days=2)
        ).isoformat()
        overflow = c.post("/api/v1/searches", json=payload)
        assert overflow.status_code == 422 and "3 origin" in overflow.json()["detail"]
        payload.update(origins=["HND"], destinations=["HND"])
        assert c.post("/api/v1/searches", json=payload).status_code == 422


def test_resolution_owner_authorization_and_missing_mapping(engine):
    with client_for(engine, [], Settings(owner_token="test-owner-" * 4)) as c:
        assert c.post("/api/v1/locations/resolve", json=major()).status_code == 401
        headers = {"Authorization": "Bearer " + "test-owner-" * 4}
        assert (
            c.post(
                "/api/v1/locations/resolve", json=major("country:US", "country"), headers=headers
            ).status_code
            == 422
        )
        assert c.post("/api/v1/locations/resolve", json=major(), headers=headers).status_code == 200


@pytest.mark.parametrize("code", ["JKT", "TYO", "LON"])
def test_legacy_arrays_reject_known_metro_only_codes_before_job_creation(engine, code):
    payload = body()
    payload["destinations"] = [code]
    with client_for(engine, [Registration(FakeProvider())]) as c:
        response = c.post("/api/v1/searches", json=payload)
        assert response.status_code == 422
        assert "Metropolitan codes" in response.json()["detail"]
