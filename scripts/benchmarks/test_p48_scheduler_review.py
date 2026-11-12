"""Offline acceptance evidence against unchanged production scheduling.

Run: .venv/bin/python -m pytest scripts/benchmarks/test_p48_scheduler_review.py -q
"""

# Imported pytest fixtures are intentionally requested by their fixture names.
# ruff: noqa: F811

import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "backend/tests/integration")
)
from cheapwings.providers.base import SingleDateRouteQuery
from cheapwings.providers.fake import FakeProvider
from cheapwings.providers.registry import Registration
from cheapwings.storage.repository import Repository, now_ms
from test_storage import engine, query  # noqa: F401


def scope(query):
    return query.model_copy(
        update={
            "destinations": ["DPS"],
            "departure_date_through": query.departure_date_from.replace(day=14),
        }
    )


async def result(reg, item, query):
    return await reg.provider.search(
        SingleDateRouteQuery(
            item.origin,
            item.destination,
            query.departure_date_from,
            True,
            False,
            query.display_currency,
        )
    )


@pytest.mark.parametrize("cache", [False, True])
@pytest.mark.asyncio
async def test_unequal_intervals_short_and_long_calls(engine, query, cache):
    repo = Repository(engine, cache_enabled=cache)
    fast = Registration(FakeProvider("fast"), minimum_interval_seconds=5)
    slow = Registration(FakeProvider("slow"), minimum_interval_seconds=10)
    q = scope(query)
    repo.create_job(q, [fast, slow])
    start = now_ms()
    a, _ = repo.claim(fast, now=start)
    b, _ = repo.claim(slow, now=start)
    assert repo.claim(fast, now=start + 100) is None
    assert repo.finish(a.id, a.lease_token, await result(fast, a, q), now=start + 1000)
    assert repo.claim(fast, now=start + 4999) is None
    a2, _ = repo.claim(fast, now=start + 5000)
    # P4.12: no per-provider ceiling. A still-running slow call does not block
    # its next start once the interval elapses, and never delays fast.
    assert repo.claim(slow, now=start + 9999) is None
    b2, _ = repo.claim(slow, now=start + 10000)
    assert repo.finish(b.id, b.lease_token, await result(slow, b, q), now=start + 12000)
    assert repo.claim(slow, now=start + 12000) is None  # paced from b2's start
    assert repo.finish(b2.id, b2.lease_token, await result(slow, b2, q), now=start + 12500)
    assert repo.finish(
        a2.id, a2.lease_token, await result(fast, a2, q), now=start + 13000
    )
    assert repo.claim(fast, now=start + 13000) is not None


@pytest.mark.parametrize("cache", [False, True])
@pytest.mark.asyncio
async def test_restart_preserves_spacing_and_provider_cooldown(engine, query, cache):
    repo = Repository(engine, cache_enabled=cache)
    a = Registration(FakeProvider("cooled"), minimum_interval_seconds=5)
    b = Registration(FakeProvider("independent"), minimum_interval_seconds=10)
    q = scope(query)
    repo.create_job(q, [a, b])
    start = now_ms()
    item, _ = repo.claim(a, now=start)
    assert repo.finish(
        item.id, item.lease_token, await result(a, item, q), now=start + 1000
    )
    restarted = Repository(engine, cache_enabled=cache)
    assert restarted.claim(a, now=start + 4999) is None
    second, _ = restarted.claim(a, now=start + 5000)
    assert restarted.finish(
        second.id,
        second.lease_token,
        error_code="http_rate_limited",
        retry_after_seconds=120,
        now=start + 6000,
    )
    restarted = Repository(engine, cache_enabled=cache)
    assert restarted.claim(a, now=start + 125999) is None
    assert restarted.claim(b, now=start + 7000) is not None
    assert restarted.claim(a, now=start + 126000) is not None


@pytest.mark.parametrize("cache", [False, True])
def test_restart_waits_for_lease_and_fences_duplicate_claims(engine, query, cache):
    repo = Repository(engine, cache_enabled=cache)
    reg = Registration(FakeProvider(), minimum_interval_seconds=5)
    repo.create_job(scope(query), [reg])
    start = now_ms()
    with ThreadPoolExecutor(max_workers=2) as pool:
        claims = list(
            pool.map(
                lambda _: Repository(engine, cache_enabled=cache).claim(
                    reg, lease_seconds=40, now=start
                ),
                range(2),
            )
        )
    assert sum(claim is not None for claim in claims) == 1
    first, _ = next(claim for claim in claims if claim is not None)
    # Budget 1 isolates lease recovery: the expired-lease item still occupies it.
    restarted = Repository(engine, cache_enabled=cache, global_capacity=1)
    restarted.sweep(now=start + 39999)
    assert restarted.claim(reg, now=start + 39999) is None
    restarted.sweep(now=start + 40000)
    recovered, _ = restarted.claim(reg, now=start + 40000)
    assert recovered.id == first.id and recovered.attempts == 2
    assert restarted.claim(reg, now=start + 40000) is None
    assert not repo.finish(
        first.id,
        first.lease_token,
        error_code="provider_unavailable",
        now=start + 40001,
    )


@pytest.mark.parametrize("cache", [False, True])
def test_cancelled_result_still_must_preserve_provider_feedback(engine, query, cache):
    repo = Repository(engine, cache_enabled=cache)
    reg = Registration(FakeProvider(), minimum_interval_seconds=5)
    q = query.model_copy(
        update={
            "destinations": ["DPS"],
            "departure_date_through": query.departure_date_from,
        }
    )
    first = repo.create_job(q, [reg])
    start = now_ms()
    item, _ = repo.claim(reg, now=start)
    repo.cancel(first.id)
    repo.finish(
        item.id,
        item.lease_token,
        error_code="http_rate_limited",
        retry_after_seconds=120,
        now=start + 1000,
    )
    repo.create_job(q, [reg])
    reopened = Repository(engine, cache_enabled=cache)
    assert reopened.claim(reg, now=start + 120999) is None
    assert reopened.claim(reg, now=start + 121000) is not None
