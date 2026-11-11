import asyncio
import threading

import pytest

from cheapwings.application.job_runner import JobRunner
from cheapwings.config import Settings
from cheapwings.providers.base import SingleDateRouteQuery
from cheapwings.providers.fake import FakeProvider
from cheapwings.providers.fli import FliProvider
from cheapwings.providers.registry import Registration, default_registry
from cheapwings.storage.repository import Repository


async def test_fli_uses_durable_shared_fetch_cancel_fencing_and_cache(engine, query):
    q = query.model_copy(
        update={"destinations": ["DPS"], "departure_date_through": query.departure_date_from}
    )
    request = SingleDateRouteQuery(
        q.origins[0],
        "DPS",
        q.departure_date_from,
        q.include_basic_economy,
        q.include_hidden_city,
        q.display_currency,
        q.point_of_sale_country,
    )
    result = await FakeProvider("fli").search(request)
    p = FliProvider(concurrency=3)
    started = threading.Event()
    release = threading.Event()
    calls = []

    def fetch(request):
        calls.append(request)
        started.set()
        release.wait(timeout=5)
        return result

    p._fetch = fetch
    p.normalize = lambda payload, request: payload
    reg = Registration(p, concurrency=3, minimum_interval_seconds=0.01)
    repo = Repository(engine, cache_enabled=True, global_capacity=9)
    first = repo.create_job(q, [reg])
    second = repo.create_job(q, [reg])
    assert repo.get_job(first.id)[1][0].operation_id == repo.get_job(second.id)[1][0].operation_id
    runner = JobRunner(repo, [reg], max_in_flight=9)
    try:
        await runner.tick()
        assert await asyncio.to_thread(started.wait, 2)
        repo.cancel(first.id)
        release.set()
        for _ in range(100):
            await runner.tick()
            if not runner.tasks and repo.get_job(second.id)[0].status == "completed":
                break
            await asyncio.sleep(0.005)
        assert len(calls) == 1
        assert repo.get_job(first.id)[0].status == "cancelled"
        assert repo.get_job(second.id)[1][0].status == "succeeded_results"
        third = repo.create_job(q, [reg])
        item = repo.get_job(third.id)[1][0]
        assert item.status == "succeeded_results" and item.result_origin == "cache"
        assert len(calls) == 1
    finally:
        release.set()
        await runner.close()


def test_fourth_registration_configuration_and_no_false_capabilities(monkeypatch):
    import importlib.util

    monkeypatch.setattr(importlib.util, "find_spec", lambda name: object())
    monkeypatch.setenv("FLI_CONCURRENCY", "3")
    monkeypatch.setenv("FLI_INTERVAL_SECONDS", "1")
    monkeypatch.setenv("ENABLED_PROVIDERS", "skiplagged,swoop,octotrip,fli")
    settings = Settings.from_env()
    registry = default_registry(settings)
    try:
        assert {r.provider.provider_id for r in registry} == {
            "skiplagged",
            "swoop",
            "octotrip",
            "fli",
        }
        fli = next(r for r in registry if r.provider.provider_id == "fli")
        assert fli.enabled and fli.concurrency == 3 and fli.minimum_interval_seconds == 1
        assert not fli.provider.capabilities.exact_reprice
        assert not fli.provider.capabilities.has_baggage_details
        assert fli.can_cache and settings.worker_max_in_flight == 9
    finally:
        for r in registry:
            if hasattr(r.provider, "blocking"):
                r.provider.blocking.close()


async def test_fli_real_normalization_api_prices_and_cache(engine, query, monkeypatch):
    pytest.importorskip("fli")
    from datetime import datetime
    from decimal import Decimal
    from types import SimpleNamespace

    from fastapi.testclient import TestClient
    from fli.search import _decoders

    from cheapwings.api.routes import create_app

    q = query.model_copy(
        update={
            "destinations": ["DPS"],
            "departure_date_through": query.departure_date_from,
            "display_currency": "IDR",
        }
    )
    flight = SimpleNamespace(
        currency="IDR",
        legs=[
            SimpleNamespace(
                airline=SimpleNamespace(name="QF", value="Qantas"),
                operating_airline=None,
                flight_number="45",
                departure_airport=SimpleNamespace(name=q.origins[0]),
                arrival_airport=SimpleNamespace(name="DPS"),
                departure_datetime=datetime.combine(
                    q.departure_date_from, datetime.min.time()
                ).replace(hour=9),
                arrival_datetime=datetime.combine(
                    q.departure_date_from, datetime.min.time()
                ).replace(hour=13),
            )
        ],
    )
    monkeypatch.setattr(_decoders, "parse_flight_row", lambda row: flight)
    calls = []

    async def transport(request):
        calls.append(request)
        return {
            "data": [None, None, [[[[], [[None, Decimal(1250000)], "synthetic"]]]], None],
            "url": "https://www.google.com/travel/flights?tfs=synthetic-request",
        }

    p = FliProvider(transport=transport)
    reg = Registration(p, concurrency=3, minimum_interval_seconds=0, live_data=True)
    settings = Settings(enabled_providers=("fli",), search_cache_enabled=True)
    app = create_app(settings=settings, registry=[reg], engine=engine)
    runner = JobRunner(app.state.repository, [reg])
    body = {
        "origins": q.origins,
        "destinations": ["DPS"],
        "departure_date_from": str(q.departure_date_from),
        "departure_date_through": str(q.departure_date_from),
        "display_currency": "IDR",
        "provider_ids": ["fli"],
    }
    try:
        with TestClient(app, base_url="http://localhost", client=("127.0.0.1", 50000)) as client:
            response = client.post("/api/v1/searches", json=body)
            assert response.status_code == 202
            path = response.json()["job_status_url"]
            for _ in range(100):
                await runner.tick()
                if not runner.tasks and client.get(path).json()["status"] == "completed":
                    break
                await asyncio.sleep(0.005)
            status = client.get(path).json()
            assert status["succeeded_provider_work_items"] == 1
            assert status["succeeded_empty"] == 0
            advertised = client.get(path + "/results?sort=lowest_advertised").json()
            trip = advertised["itineraries"][0]
            offer = trip["offers"][0]
            assert trip["origin"] == q.origins[0] and trip["destination"] == "DPS"
            assert Decimal(offer["comparable_amount"]) == Decimal(1250000)
            assert offer["comparable_currency"] == "IDR"
            assert offer["price_status"] == "indicative"
            assert offer["link_scope"] == "generic_search"
            assert "provider_quote_handle" not in offer
            assert client.get(path + "/results?sort=best_checked").json()["itineraries"] == []
            second = client.post("/api/v1/searches", json=body).json()["job_status_url"]
            reused = client.get(second + "/results?sort=lowest_advertised").json()
            assert reused["itineraries"][0]["offers"][0]["retrieved_at"] == offer["retrieved_at"]
            assert len(calls) == 1
    finally:
        await runner.close()


async def test_missing_fli_payload_is_failure_and_never_cached(engine, query):
    pytest.importorskip("fli")
    from sqlalchemy import func, select
    from sqlalchemy.orm import Session

    from cheapwings.storage.models import ProviderResultCache

    q = query.model_copy(
        update={"destinations": ["DPS"], "departure_date_through": query.departure_date_from}
    )

    async def transport(request):
        return {"data": [None, None, None, None]}

    p = FliProvider(transport=transport)
    reg = Registration(p, concurrency=3, minimum_interval_seconds=0)
    repo = Repository(engine, cache_enabled=True)
    job = repo.create_job(q, [reg])
    runner = JobRunner(repo, [reg], max_attempts=1)
    try:
        for _ in range(100):
            await runner.tick()
            if not runner.tasks and repo.get_job(job.id)[0].status == "failed":
                break
            await asyncio.sleep(0.005)
        work = repo.get_job(job.id)[1][0]
        assert work.status == "failed_terminal" and work.last_error_code == "schema_changed"
        with Session(engine) as session:
            assert session.scalar(select(func.count()).select_from(ProviderResultCache)) == 0
    finally:
        await runner.close()


def test_missing_optional_fli_is_disabled_with_install_reason(monkeypatch):
    import importlib.util

    actual = importlib.util.find_spec
    monkeypatch.setattr(
        importlib.util, "find_spec", lambda name: None if name == "fli" else actual(name)
    )
    registry = default_registry(Settings(enabled_providers=("fli",)))
    try:
        fli = next(r for r in registry if r.provider.provider_id == "fli")
        assert not fli.enabled and "fli" in fli.disabled_reason
        assert "backend[live]" in fli.disabled_reason
    finally:
        for reg in registry:
            if hasattr(reg.provider, "blocking"):
                reg.provider.blocking.close()
