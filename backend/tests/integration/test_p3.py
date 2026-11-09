from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from test_worker import drain, single

from cheapwings.api.routes import create_app
from cheapwings.application.job_runner import JobRunner
from cheapwings.application.search_service import results_projection, status_projection
from cheapwings.config import Settings
from cheapwings.domain.evidence import SourceEvidence
from cheapwings.domain.money import Money
from cheapwings.providers.base import ProviderRepriceResult
from cheapwings.providers.common import json_payload
from cheapwings.providers.fake import FakeProvider
from cheapwings.providers.registry import Registration, default_registry
from cheapwings.providers.skiplagged import SkiplaggedProvider
from cheapwings.providers.swoop import SwoopProvider
from cheapwings.storage.db import write_session
from cheapwings.storage.models import FareQuote, FXRow, QuoteRevision, SearchJob
from cheapwings.storage.repository import Repository, now_ms

FIXTURES = Path(__file__).parents[3] / 'contracts/fixtures/provider'


def fixture(name):
    return json_payload((FIXTURES / name).read_text())


class CheckingFake(FakeProvider):
    def __init__(self, *, unavailable=0, estimated=False, mismatch=False):
        super().__init__()
        self.capabilities = replace(self.capabilities, exact_reprice=True)
        self.calls = 0
        self.unavailable = unavailable
        self.estimated = estimated
        self.mismatch = mismatch

    async def search(self, query):
        result = await super().search(query)
        offers = tuple(tuple(replace(o, evidence=SourceEvidence(
            fee_completeness='known_total', point_of_sale_country='ID')) for o in batch)
            for batch in result.offers_by_itinerary_index)
        return replace(result, offers_by_itinerary_index=offers)

    async def reprice(self, request):
        self.calls += 1
        if self.calls <= self.unavailable:
            return ProviderRepriceResult((), (), False, False)
        offer = request.offer
        price = Money(offer.amount_original.amount + Decimal(10), offer.amount_original.currency)
        changed = replace(offer, amount_original=price, comparable_amount=price,
                          is_estimate=self.estimated,
                          fare_family='different-family' if self.mismatch else offer.fare_family)
        return ProviderRepriceResult((changed,), request.segments, True, True)


async def test_durable_reprice_revisions_exact_and_coverage(engine, query):
    provider = CheckingFake()
    reg = [Registration(provider, minimum_interval_seconds=0)]
    repo = Repository(engine)
    job = repo.create_job(single(query), reg, reprice_budget=2)
    await drain(JobRunner(repo, reg), repo, job.id)
    status = status_projection(repo, job.id)
    assert status.status == 'completed'
    assert status.total_provider_work_items == 1
    assert status.covered_route_date_combinations == 1
    assert status.exact_reprice_attempted == 2
    assert status.exact_reprice_succeeded == 2
    payload = results_projection(repo, job.id, 'best_checked')
    assert all(o.price_status == 'repriced_exact' for o in payload.itineraries[0].offers)
    with Session(engine) as s:
        assert s.scalar(select(func.count()).select_from(FareQuote)) == 2
        assert s.scalar(select(func.count()).select_from(QuoteRevision)) == 4
        amounts = s.scalars(select(QuoteRevision.amount_decimal_text).order_by(QuoteRevision.id)).all()
        assert Decimal(amounts[2]) in (Decimal(amounts[0])+10, Decimal(amounts[1])+10)


async def test_unavailable_reprice_follows_next_candidate_and_estimate(engine, query):
    provider = CheckingFake(unavailable=1, estimated=True)
    reg = [Registration(provider, minimum_interval_seconds=0)]
    repo = Repository(engine)
    job = repo.create_job(single(query), reg, reprice_budget=2)
    await drain(JobRunner(repo, reg), repo, job.id)
    assert provider.calls == 2
    assert status_projection(repo, job.id).exact_reprice_succeeded == 0
    results = results_projection(repo, job.id, 'lowest_advertised')
    assert results.itineraries[0].ranked_quote_id
    assert any(o.price_status == 'changed_or_unavailable' for o in results.itineraries[0].offers)
    assert any(o.price_status == 'indicative' for o in results.itineraries[0].offers)


async def test_reprice_fare_mismatch_never_inherits_exact(engine, query):
    provider = CheckingFake(mismatch=True)
    reg = [Registration(provider, minimum_interval_seconds=0)]
    repo = Repository(engine)
    job = repo.create_job(single(query), reg, reprice_budget=2)
    await drain(JobRunner(repo, reg), repo, job.id)
    assert status_projection(repo, job.id).exact_reprice_succeeded == 0
    results = results_projection(repo, job.id, 'lowest_advertised')
    assert all(o.price_status != 'repriced_exact' for g in results.itineraries for o in g.offers)


async def test_recorded_real_adapters_api_summary_fx_and_expiry(engine):
    skip = fixture('skiplagged_probe_20261109T123430Z.json')['search_structured_content']
    swoop = fixture('swoop_probe_20261109T123521Z.json')
    async def sk_transport(args):
        return skip
    async def sw_transport(q):
        return dict(swoop['search_result'], results=swoop['search_result']['results'][:1])
    async def price(selector):
        return swoop['price_result']
    zone = lambda code: {'MEL':'Australia/Melbourne','SYD':'Australia/Sydney','DPS':'Asia/Makassar'}[code]
    reg = [Registration(SkiplaggedProvider(sk_transport), minimum_interval_seconds=0, live_data=True),
           Registration(SwoopProvider(sw_transport, price, zone), minimum_interval_seconds=0, live_data=True)]
    app = create_app(Settings(), reg, engine)
    with TestClient(app, base_url='http://localhost', client=('127.0.0.1', 5000)) as client:
        response = client.post('/api/v1/searches', json={
            'origins':['MEL'], 'destinations':['DPS'], 'departure_date_from':'2026-12-16',
            'departure_date_through':'2026-12-16', 'display_currency':'IDR'})
        assert response.status_code == 202
        job_id = response.json()['job_id']
        repo = app.state.repository
        await drain(JobRunner(repo, reg), repo, job_id)
        status = client.get(f'/api/v1/searches/{job_id}').json()
        assert status['total_provider_work_items'] == 2
        assert status['covered_route_date_combinations'] == 1
        assert status['exact_reprice_attempted'] == 1
        assert status['exact_reprice_succeeded'] == 0
        assert status['data_expires_at'] is not None
        safe = client.get(f'/api/v1/searches/{job_id}/results').json()
        assert safe['itineraries'] == []
        advertised = client.get(f'/api/v1/searches/{job_id}/results?sort=lowest_advertised').json()
        assert len(advertised['itineraries']) == 6
        unmatched = next(i for i in advertised['itineraries'] if i['identity_confidence']=='insufficient_identity')
        assert unmatched['segments'] == [] and unmatched['warnings']
        assert unmatched['offers'][0]['fx_rate'] == '18108.7'
        assert unmatched['offers'][0]['attribution'] == 'Skiplagged'
        assert 'selector' not in str(advertised) and 'booking_token' not in str(advertised)
        with Session(engine) as s:
            assert s.scalar(select(func.count()).select_from(FXRow)) == 5
        with write_session(engine) as s:
            s.get(SearchJob, job_id).data_expires_at = now_ms()-1
        assert client.get(f'/api/v1/searches/{job_id}/results').status_code == 410
        with Session(engine) as s:
            assert s.scalar(select(func.count()).select_from(FareQuote)) == 0
            assert s.scalar(select(func.count()).select_from(QuoteRevision)) == 0
            assert s.scalar(select(func.count()).select_from(FXRow)) == 0


def test_registry_scope_and_dependency_gating():
    registry = default_registry(Settings(enabled_providers=('skiplagged','swoop'), use_scope='public'))
    assert all(r.unavailable_reason == 'terms_not_approved for configured scope' for r in registry)
    assert all(r.live_data and r.retention_seconds == 3600 for r in registry)
    import pytest
    with pytest.raises(ValueError):
        Settings(enabled_providers=('fake','swoop'))
