"""P7.4 Discover API: create → poll → completed with the fake provider; Search responses unchanged."""

import asyncio
from dataclasses import replace

from fastapi.testclient import TestClient
from test_worker import drain

from cheapwings.api.routes import create_app
from cheapwings.application import contracts as dto
from cheapwings.application.job_runner import JobRunner
from cheapwings.config import Settings
from cheapwings.providers.fake import FakeProvider
from cheapwings.providers.registry import Registration


def discover_data(**kw):
    return {"origins": ["CGK"], "departure_date_from": "2027-03-01", "departure_date_through": "2027-03-02",
            "display_currency": "IDR", **kw}


def registry():
    fake = FakeProvider(provider_id="disc")
    fake.capabilities = replace(fake.capabilities, destination_discovery=True)
    return [Registration(fake, minimum_interval_seconds=0)]


def client_for(engine, reg):
    return TestClient(create_app(Settings(), reg, engine), base_url="http://localhost", client=("127.0.0.1", 50000))


def test_discover_create_poll_results(engine):
    reg = registry()
    with client_for(engine, reg) as client:
        response = client.post("/api/v1/discover", json=discover_data())
        assert response.status_code == 202
        created = dto.DiscoverCreated.model_validate_json(response.text)
        assert created.discovery_calls == 2 and created.enabled_detailed_providers == ["disc"]
        assert response.headers["location"] == f"/api/v1/discover/{created.job_id}"
        early = dto.DiscoverJob.model_validate_json(client.get(response.headers["location"]).text)
        assert (early.phase, early.discovery.calls_planned, early.discovery.calls_done) == ("discovering", 2, 0)
        repo = client.app.state.repository
        asyncio.run(drain(JobRunner(repo, reg), repo, created.job_id))
        job = dto.DiscoverJob.model_validate_json(client.get(response.headers["location"]).text)
        assert (job.status, job.phase) == ("completed", "done")
        d = job.discovery
        assert (d.calls_planned, d.calls_done, d.calls_failed, d.outcome) == (2, 2, 0, "planned")
        assert d.counts["selected"] == 2 and d.discovered_destinations == 2
        assert (job.checked_route_dates, job.total_checks, job.succeeded_checks) == (2, 2, 2)
        assert any("2 discovered destinations" in w for w in job.warnings)
        assert job.query.origins == ["CGK"]
        results = dto.Results.model_validate_json(client.get(f"/api/v1/discover/{created.job_id}/results").text)
        # P7.5: the shortlist in plan order, comparable amounts in the display currency (40/50 USD × 16000).
        assert [(l.destination, l.date, l.comparable_amount) for l in d.shortlist] == [
            ("DPS", "2027-03-01", "640000"), ("SIN", "2027-03-01", "800000")]
        # P7.5 review fix: the cheapest checked fare per shortlisted route/date, computed on the server
        # from every stored quote (not just the first results page).
        for l in d.shortlist:
            fares = [o.comparable_amount for i in results.itineraries for o in i.offers
                     if i.destination == l.destination and i.departure_local.date().isoformat() == l.date]
            assert l.checked_amount == str(min(fares, key=lambda x: __import__("decimal").Decimal(x)))
            assert l.checked_itinerary_id
        results = dto.Results.model_validate_json(client.get(f"/api/v1/discover/{created.job_id}/results").text)
        assert {i.destination for i in results.itineraries} >= {"DPS", "SIN"}
        # A Discover job is not a Search job, and the other way round.
        assert client.get(f"/api/v1/searches/{created.job_id}").status_code == 404


def test_discover_validation_and_cancel(engine):
    reg = registry()
    with client_for(engine, reg) as client:
        assert client.post("/api/v1/discover", json=discover_data(departure_date_through="2027-04-30")).status_code == 422
        assert client.post("/api/v1/discover", json=discover_data(departure_date_from="2020-01-01")).status_code == 422
        assert client.post("/api/v1/discover", json=discover_data(budget="-5")).status_code == 422
        created = client.post("/api/v1/discover", json=discover_data(budget="1500000")).json()
        cancelled = dto.DiscoverJob.model_validate_json(client.post(f"/api/v1/discover/{created['job_id']}/cancel").text)
        assert cancelled.status == "cancelled"
        assert cancelled.query.budget is not None


def test_no_discovery_source_is_422(engine):
    with client_for(engine, [Registration(FakeProvider(), minimum_interval_seconds=0)]) as client:
        response = client.post("/api/v1/discover", json=discover_data())
        assert response.status_code == 422
        assert "discovery" in response.json()["detail"]


def test_search_status_body_unchanged(engine):
    reg = [Registration(FakeProvider(), minimum_interval_seconds=0)]
    with client_for(engine, reg) as client:
        created = client.post("/api/v1/searches", json={
            "origins": ["CGK"], "destinations": ["DPS"], "departure_date_from": "2027-03-01",
            "departure_date_through": "2027-03-01", "display_currency": "IDR"}).json()
        body = client.get(f"/api/v1/searches/{created['job_id']}").json()
        assert "kind" not in body and "discovery" not in body
        assert client.get(f"/api/v1/discover/{created['job_id']}").status_code == 404
