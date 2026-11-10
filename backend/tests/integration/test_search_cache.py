import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from test_api import client_for, request_data
from test_worker import drain, single

from cheapwings.application.job_runner import JobRunner
from cheapwings.application.search_service import results_projection
from cheapwings.config import Settings
from cheapwings.domain.query import MaxStops
from cheapwings.providers.base import SingleDateRouteQuery
from cheapwings.providers.fake import FakeProvider
from cheapwings.providers.registry import Registration
from cheapwings.storage.cache import RESULT
from cheapwings.storage.db import write_session
from cheapwings.storage.models import (
    FareQuote,
    OperationAttempt,
    ProviderOperation,
    ProviderResultCache,
    QuoteRevision,
)
from cheapwings.storage.repository import CapacityExceeded, Repository, now_ms


class Counted(FakeProvider):
    calls = 0

    async def search(self, request):
        self.calls += 1
        return await super().search(request)


def setup(engine):
    provider = Counted()
    reg = Registration(provider, minimum_interval_seconds=0, retention_seconds=3600)
    return Repository(engine, cache_enabled=True), reg


async def finish(repo, reg, job):
    await drain(JobRunner(repo, [reg]), repo, job.id)


async def test_cached_snapshot_keeps_money_times_ids_and_absolute_expiry(engine, query):
    repo, reg = setup(engine)
    first = repo.create_job(single(query), [reg], retention_seconds=3600)
    await finish(repo, reg, first)
    original = results_projection(repo, first.id, "lowest_advertised").itineraries[0]
    second = repo.create_job(single(query), [reg], retention_seconds=3600, max_hourly=1)
    cached = results_projection(repo, second.id, "lowest_advertised").itineraries[0]
    assert reg.provider.calls == 1
    assert second.id != first.id and cached.itinerary_id != original.itinerary_id
    assert cached.offers[0].amount_original == original.offers[0].amount_original
    assert cached.offers[0].retrieved_at == original.offers[0].retrieved_at
    assert cached.offers[0].result_origin == "cache"
    assert second.data_expires_at == first.data_expires_at
    item = repo.get_job(second.id)[1][0]
    assert item.status == "succeeded_results" and item.attempts == 0
    assert item.reused_at and item.cache_fresh_until
    with Session(engine) as s:
        snapshot = s.scalar(select(ProviderResultCache))
        assert all(
            not offer.provider_quote_handle
            for offers in RESULT.validate_json(snapshot.payload_json).offers_by_itinerary_index
            for offer in offers
        )
        assert (
            s.scalar(
                select(func.count())
                .select_from(QuoteRevision)
                .where(QuoteRevision.reason != "initial_search")
            )
            == 0
        )


async def test_simultaneous_admission_coalesces_and_cancel_primary_isolated(engine, query):
    repo, reg = setup(engine)
    q = single(query)
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = list(pool.map(lambda _: repo.create_job(q, [reg]), range(2)))
    one = repo.get_job(jobs[0].id)[1][0]
    two = repo.get_job(jobs[1].id)[1][0]
    assert one.operation_id == two.operation_id
    release = asyncio.Event()
    search = reg.provider.search

    async def slow(request):
        await release.wait()
        return await search(request)

    reg.provider.search = slow
    runner = JobRunner(repo, [reg])
    await runner.tick()
    repo.cancel(jobs[0].id)
    release.set()
    await asyncio.gather(*runner.tasks)
    await drain(runner, repo, jobs[1].id)
    assert reg.provider.calls == 1
    assert repo.get_job(jobs[0].id)[0].status == "cancelled"
    assert repo.get_job(jobs[1].id)[0].status == "completed"
    assert results_projection(repo, jobs[0].id, "lowest_advertised").itineraries == []


async def test_force_refresh_and_key_policy_isolation(engine, query):
    repo, reg = setup(engine)
    q = single(query)
    first = repo.create_job(q, [reg])
    await finish(repo, reg, first)
    second = repo.create_job(q, [reg], cache_mode="refresh")
    assert repo.get_job(second.id)[1][0].result_origin == "live"
    await finish(repo, reg, second)
    assert reg.provider.calls == 2
    for update in (
        {"display_currency": "USD"},
        {"include_hidden_city": True},
        {"checked_bags_required": True},
        {"max_stops": MaxStops.NONSTOP},
        {"point_of_sale_country": "ID"},
    ):
        changed = q.model_copy(update=update)
        job = repo.create_job(changed, [reg])
        assert repo.get_job(job.id)[1][0].operation_id
        await finish(repo, reg, job)
    assert reg.provider.calls == 7
    reg = replace(reg, usage_policy_reviewed_on="changed")
    job = repo.create_job(q, [reg])
    assert repo.get_job(job.id)[1][0].result_origin == "live"


async def test_exact_ttl_boundary_misses_and_limits_bound_storage(engine, query, monkeypatch):
    repo, reg = setup(engine)
    repo.cache_max_entries = 1
    first = repo.create_job(single(query), [reg])
    await finish(repo, reg, first)
    with Session(engine) as s:
        expiry = s.scalar(select(ProviderResultCache)).fresh_until
    monkeypatch.setattr("cheapwings.storage.repository.now_ms", lambda: expiry)
    second = repo.create_job(single(query), [reg])
    assert repo.get_job(second.id)[1][0].result_origin == "live"
    repo.sweep(now=expiry)
    with Session(engine) as s:
        assert s.scalar(select(func.count()).select_from(ProviderResultCache)) == 0


@pytest.mark.parametrize("kind", ["partial", "unknown", "unpriced"])
async def test_incomplete_results_never_become_cache_hits(engine, query, kind):
    repo, reg = setup(engine)
    original = reg.provider.search

    async def partial(request):
        result = await original(request)
        return replace(
            result,
            provider_complete=None if kind == "unknown" else kind == "unpriced",
            unpriced_candidate_count=1 if kind == "unpriced" else 0,
        )

    reg.provider.search = partial
    job = repo.create_job(single(query), [reg])
    await finish(repo, reg, job)
    with Session(engine) as s:
        assert s.scalar(select(func.count()).select_from(ProviderResultCache)) == 0
    second = repo.create_job(single(query), [reg])
    assert repo.get_job(second.id)[1][0].operation_id


async def test_restart_fences_shared_fetch_and_rolls_back_bad_store(engine, query):
    repo, reg = setup(engine)
    q = single(query)
    repo.create_job(q, [reg])
    old, _ = repo.claim(reg, lease_seconds=1)
    result = await reg.provider.search(
        SingleDateRouteQuery("MEL", "DPS", q.departure_date_from, True, False, "IDR")
    )
    repo.sweep(now=now_ms() + 2000)
    assert not repo.finish(old.id, old.lease_token, result)
    new, _ = repo.claim(reg)
    store = repo._store_results

    def fail(*args):
        store(*args)
        raise RuntimeError("simulated transaction rollback")

    repo._store_results = fail
    with pytest.raises(RuntimeError):
        repo.finish(new.id, new.lease_token, result)
    with Session(engine) as s:
        assert s.scalar(select(func.count()).select_from(FareQuote)) == 0
        assert s.scalar(select(func.count()).select_from(ProviderResultCache)) == 0
    repo._store_results = store
    assert repo.finish(new.id, new.lease_token, result)
    assert not repo.finish(new.id, new.lease_token, result)
    with Session(engine) as s:
        assert [
            a.outcome for a in s.scalars(select(OperationAttempt).order_by(OperationAttempt.id))
        ] == ["lease_expired", "succeeded_results"]


async def test_requests_limited_even_when_fully_cached_and_feature_off_misses(engine, query):
    repo, reg = setup(engine)
    q = single(query)
    first = repo.create_job(q, [reg])
    await finish(repo, reg, first)
    with pytest.raises(CapacityExceeded):
        repo.create_job(q, [reg], max_requests=1)
    repo.cache_enabled = False
    second = repo.create_job(q, [reg])
    item = repo.get_job(second.id)[1][0]
    assert item.operation_id is None and item.status == "pending"


def test_provider_selection_backend_only_and_old_requests_compatible(engine):
    registry = [Registration(FakeProvider()), Registration(FakeProvider(provider_id="second"))]
    with client_for(engine, registry, Settings(search_cache_enabled=True)) as client:
        data = {**request_data(), "provider_ids": ["second"], "cache_mode": "refresh"}
        response = client.post("/api/v1/searches", json=data)
        assert response.status_code == 202
        status = client.get(response.headers["location"]).json()
        assert status["provider_ids"] == ["second"] and status["cache_mode"] == "refresh"
        assert {i["provider_id"] for i in status["coverage"]} == {"second"}
        for ids in ([], ["fake", "fake"], ["untrusted"], ["https://example.org"]):
            assert (
                client.post("/api/v1/searches", json={**data, "provider_ids": ids}).status_code
                == 422
            )


async def test_empty_success_cached_but_errors_retry_and_never_cached(engine, query):
    from cheapwings.domain.coverage import WorkStatus
    from cheapwings.providers.fake import ScriptedOutcome

    repo, reg = setup(engine)
    q = single(query)
    reg.provider.script(
        "MEL", "DPS", q.departure_date_from, ScriptedOutcome(WorkStatus.SUCCEEDED_EMPTY)
    )
    first = repo.create_job(q, [reg])
    await finish(repo, reg, first)
    second = repo.create_job(q, [reg])
    assert repo.get_job(second.id)[1][0].status == "succeeded_empty"
    changed = q.model_copy(update={"display_currency": "USD"})
    job = repo.create_job(changed, [reg])
    operation, _ = repo.claim(reg)
    start = now_ms()
    repo.finish(
        operation.id,
        operation.lease_token,
        error_code="http_rate_limited",
        retry_after_seconds=120,
        now=start,
    )
    assert repo.claim(reg, now=start + 119999) is None
    new, _ = repo.claim(reg, now=start + 120000)
    repo.finish(new.id, new.lease_token, error_code="auth_denied", now=start + 120001)
    assert repo.get_job(job.id)[0].status == "failed"
    with Session(engine) as s:
        assert s.scalar(select(func.count()).select_from(ProviderResultCache)) == 1


async def test_refresh_does_not_join_old_fetch_and_all_cancelled_calls_keep_slot(engine, query):
    repo, reg = setup(engine)
    q = single(query)
    first = repo.create_job(q, [reg])
    old, _ = repo.claim(reg)
    # Ensure the refresh request is later than the original operation's creation timestamp.
    with write_session(engine) as s:
        operation = s.get(ProviderOperation, old.id)
        operation.created_at -= 1
    refresh = repo.create_job(q, [reg], cache_mode="refresh")
    assert repo.get_job(refresh.id)[1][0].operation_id != old.id
    repo.cancel(first.id)
    assert repo.claim(reg) is None
    result = await reg.provider.search(
        SingleDateRouteQuery("MEL", "DPS", q.departure_date_from, True, False, "IDR")
    )
    repo.finish(old.id, old.lease_token, result)
    with Session(engine) as s:
        assert s.scalar(select(func.count()).select_from(ProviderResultCache)) == 0
    await finish(repo, reg, refresh)
    assert reg.provider.calls == 2


async def test_cache_eviction_bytes_policy_revocation_and_filter_reapplication(engine, query):
    repo, reg = setup(engine)
    repo.cache_max_entries = 1
    q = single(query)
    for currency in ("IDR", "USD"):
        job = repo.create_job(q.model_copy(update={"display_currency": currency}), [reg])
        await finish(repo, reg, job)
    with Session(engine) as s:
        assert s.scalar(select(func.count()).select_from(ProviderResultCache)) == 1
        assert s.scalar(select(ProviderResultCache)).provider_id == reg.provider.provider_id
    repo.cache_max_bytes = 1
    repo.sweep()
    with Session(engine) as s:
        assert s.scalar(select(func.count()).select_from(ProviderResultCache)) == 0
    pending = repo.create_job(q, [reg])
    claim, _ = repo.claim(reg)
    repo.reconcile_registry([replace(reg, permitted_to_aggregate=False)])
    assert repo.get_job(pending.id)[0].status == "failed"
    assert not repo.finish(claim.id, claim.lease_token, error_code="auth_denied")


async def test_absolute_retention_deadline_expires_inherited_job_and_purges(
    engine, query, monkeypatch
):
    from cheapwings.storage.verification import ResultsExpired

    repo, reg = setup(engine)
    first = repo.create_job(single(query), [reg], retention_seconds=60)
    await finish(repo, reg, first)
    second = repo.create_job(single(query), [reg], retention_seconds=3600)
    assert second.data_expires_at == first.data_expires_at
    monkeypatch.setattr(
        "cheapwings.application.search_service.now_ms", lambda: first.data_expires_at
    )
    with pytest.raises(ResultsExpired):
        results_projection(repo, second.id, "lowest_advertised")
    repo.purge_expired(now=first.data_expires_at)
    repo.sweep(now=first.data_expires_at)
    with Session(engine) as s:
        assert s.scalar(select(func.count()).select_from(FareQuote)) == 0
        assert s.scalar(select(func.count()).select_from(ProviderResultCache)) == 0


async def test_reprice_revisions_are_never_replayed_from_mutable_quote_rows(engine, query):
    repo, reg = setup(engine)
    first = repo.create_job(single(query), [reg])
    await finish(repo, reg, first)
    before = results_projection(repo, first.id, "lowest_advertised").itineraries[0].offers[0]
    with write_session(engine) as s:
        quote = s.scalar(select(FareQuote).where(FareQuote.job_id == first.id))
        quote.canonical_json = {**quote.canonical_json, "seller": "SYNTHETIC CHANGED SELLER"}
    second = repo.create_job(single(query), [reg])
    after = results_projection(repo, second.id, "lowest_advertised").itineraries[0].offers[0]
    assert after.seller == before.seller and after.result_origin == "cache"
