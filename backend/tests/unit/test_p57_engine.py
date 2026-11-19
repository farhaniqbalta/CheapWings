"""P5.7 binding gates against Python references frozen before the cutover."""

import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import cheapwings_core as core
import pytest
from backend.tests.references import fingerprint, ranking, scope
from backend.tests.references.catalog import MajorSelection as ReferenceSelection
from backend.tests.references.catalog import catalog as reference_catalog

from cheapwings.domain.itinerary import compute_fingerprint
from cheapwings.domain.scope import plan_scope
from cheapwings.domain.segments import FlightSegment
from cheapwings.engine.ranking import best_checked_deal, lowest_advertised
from cheapwings.locations.catalog import MajorSelection, catalog


def test_engine_bindings_exist():
    for name in ("fingerprint", "rank_offers", "plan_search", "plan_scope", "LocationCatalog"):
        assert hasattr(core, name), name


@pytest.mark.parametrize("offset", [20700, -12600, 30, -0.25, 30.125])
def test_fingerprint_matches_frozen_reference(offset):
    at = datetime(2027, 1, 1, 10, 30, 15, 123456, timezone(timedelta(seconds=offset)))
    segments = (
        FlightSegment("QF", "AA", "123", "MEL", "SIN", at, at + timedelta(hours=3), 0),
        FlightSegment(
            "QF", "QF", "124", "SIN", "DPS", at + timedelta(hours=4), at + timedelta(hours=6), 1
        ),
    )
    assert compute_fingerprint(segments) == fingerprint.compute_fingerprint(segments)


@pytest.mark.parametrize("days", [-2, -1, 0, 1, 120, 121])
@pytest.mark.parametrize(
    "origins,destinations", [([], []), (["MEL"], []), (["mel", " MEL ", "DPS"], ["MEL", "DPS"])]
)
def test_scope_preview_matches_reference(days, origins, destinations):
    start = date(2027, 1, 1)
    end = start + timedelta(days=days)
    assert plan_scope(origins, destinations, start, end, ["a", "a", "b"]) == scope.plan_scope(
        origins, destinations, start, end, ["a", "a", "b"]
    )


@pytest.mark.parametrize(
    "text,within",
    [("tokyo", None), ("a", None), ("", "country:JP"), ("cgk", None), ("Tokyoा", None)],
)
def test_catalog_preserves_complete_records_and_order(text, within):
    assert catalog().search(text, within) == reference_catalog().search(text, within)


def test_catalog_major_messages_and_order():
    for version, kind, location in [
        (catalog().version, "country", "country:JP"),
        ("old", "city", "metro:JP:TYO"),
        (catalog().version, "city", "country:JP"),
        (catalog().version, "city", "missing"),
    ]:
        selection = MajorSelection(type=kind, location_id=location, catalog_version=version)
        try:
            expected = reference_catalog().resolve(ReferenceSelection(**selection.model_dump()))
        except ValueError as exc:
            with pytest.raises(ValueError, match=re.escape(str(exc))):
                catalog().resolve(selection)
        else:
            assert catalog().resolve(selection).model_dump() == expected.model_dump()


def test_ranking_duplicate_ids_and_stable_ties():
    from cheapwings.domain.offer import ComparisonStatus, PriceStatus, ThreeValued

    offers = [
        SimpleNamespace(
            quote_id="same",
            price_status=status,
            hidden_city=hidden,
            comparison_status=comparison,
            comparable_amount=SimpleNamespace(amount=Decimal(amount)) if amount else None,
        )
        for status, hidden, comparison, amount in [
            (
                PriceStatus.INDICATIVE,
                ThreeValued.UNKNOWN,
                ComparisonStatus.ELIGIBLE_TOTAL_KNOWN,
                "10.0",
            ),
            (
                PriceStatus.RECENT_SEARCH,
                ThreeValued.NO,
                ComparisonStatus.ELIGIBLE_TOTAL_KNOWN,
                "10.00",
            ),
            (
                PriceStatus.RECENT_SEARCH,
                ThreeValued.NO,
                ComparisonStatus.ELIGIBLE_TOTAL_KNOWN,
                "10",
            ),
            (PriceStatus.INDICATIVE, ThreeValued.YES, ComparisonStatus.ELIGIBLE_TOTAL_KNOWN, "1"),
            (PriceStatus.INDICATIVE, ThreeValued.NO, ComparisonStatus.ELIGIBLE_TOTAL_KNOWN, None),
        ]
    ]
    groups = [SimpleNamespace(offers=offers[:2]), SimpleNamespace(offers=offers[2:])]
    for actual, reference in [
        (best_checked_deal, ranking.best_checked_deal),
        (lowest_advertised, ranking.lowest_advertised),
    ]:
        assert [(id(r.group), id(r.offer)) for r in actual(groups)] == [
            (id(r.group), id(r.offer)) for r in reference(groups)
        ]


def test_ranking_keeps_all_decimal_digits():
    # Rust's fixed-precision Decimal must not round away the order of valid Python amounts.
    amounts = [
        "1.00000000000000000000000000002",
        "1.00000000000000000000000000001",
        "1E+40",
        "-1E+40",
    ]
    rows = [("recent_search", "no", "eligible_total_known", amount) for amount in amounts]
    assert core.rank_offers(rows, True) == [3, 1, 0, 2]


def test_fixture_generators_do_not_call_rust_engine(monkeypatch):
    import importlib.util
    from pathlib import Path

    spec = importlib.util.spec_from_file_location(
        "p57_generator", Path(__file__).resolve().parents[3] / "scripts/gen_core_fixtures.py"
    )
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)

    def forbidden(*args, **kwargs):
        raise AssertionError("reference generation called Rust")

    for name in ("fingerprint", "rank_offers", "plan_search", "plan_scope", "LocationCatalog"):
        monkeypatch.setattr(core, name, forbidden)
    assert len(generator.fingerprint_cases(5)) == 5
    assert len(generator.ranking_cases(5)) == 5
    assert len(generator.planning_cases(5)) == 11
    assert generator.location_search_cases()
    assert generator.location_major_cases()


def test_frozen_cross_language_engine_fixtures():
    import json
    from pathlib import Path

    fixtures = json.loads(
        (
            Path(__file__).resolve().parents[3] / "contracts/fixtures/core/core_fixtures.json"
        ).read_text()
    )
    for case in fixtures["fingerprint"]:

        def instant(t):
            return datetime(
                t["y"],
                t["mo"],
                t["d"],
                t["h"],
                t["mi"],
                t["s"],
                t["us"],
                timezone(timedelta(seconds=t["offset"])),
            )

        segments = tuple(
            FlightSegment(
                s["marketing"],
                s["operating"],
                s["flight"],
                s["origin"],
                s["destination"],
                instant(s["depart"]),
                instant(s["arrive"]),
                s["ordinal"],
            )
            for s in case["segments"]
        )
        assert compute_fingerprint(segments) == case["expect"]
    for case in fixtures["ranking"]:
        offers = [offer for group in case["groups"] for offer in group]
        rows = [
            (o["price_status"], o["hidden_city"], o["comparison_status"], o["amount"])
            for o in offers
        ]
        for best, key in [(True, "best"), (False, "lowest")]:
            assert [offers[i]["id"] for i in core.rank_offers(rows, best)] == case[key]
    for case in fixtures["planning"]:
        args = (case["origins"], case["destinations"], case["from"], case["through"], case["max"])
        if isinstance(case["expect"], dict):
            message = {
                "invalid_airport": "invalid IATA code",
                "no_airports": "at least one airport code",
                "dates_reversed": "end date is before start date",
                "invalid_date": "invalid date",
                "same_airport": "origin and destination cannot both be",
                "too_many": "combinations exceeds the maximum",
            }[case["expect"]["error"]]
            with pytest.raises(ValueError, match=message):
                core.plan_search(*args)
        else:
            assert [
                dict(zip(("origin", "destination", "date"), r)) for r in core.plan_search(*args)
            ] == case["expect"]


@pytest.mark.parametrize("name,text", [("ΟΣ", "ος"), ("Ꭰ", "ꭰ"), ("ᾳ", "αι"), ("ᲀ", "в")])
def test_catalog_unicode_casefold_matches_reference(name, text):
    from copy import deepcopy

    from backend.tests.references.catalog import LocationCatalog as ReferenceCatalog

    from cheapwings.locations.catalog import LocationCatalog

    data = deepcopy(catalog().data)
    data["entities"][0]["name"] = name
    assert LocationCatalog(data).search(text) == ReferenceCatalog(data).search(text)


def test_python_whitespace_semantics_for_catalog_and_scope():
    text = "\x1cTokyo\x1f"
    assert catalog().search(text) == reference_catalog().search(text)
    start = date(2027, 1, 1)
    assert plan_scope(["\x1cMEL\x1f"], ["MEL"], start, start) == scope.plan_scope(
        ["\x1cMEL\x1f"], ["MEL"], start, start
    )


@pytest.mark.parametrize(
    "amount", ["NaN", "broken", "1e999999999999999999999", "0.1e-9223372036854775808"]
)
def test_invalid_ranking_amount_raises(amount):
    with pytest.raises(ValueError, match="Invalid ranking amount"):
        core.rank_offers([("recent_search", "no", "eligible_total_known", amount)], True)


def test_fold_matches_assigned_python_unicode():
    import unicodedata

    from backend.tests.references.catalog import fold

    for point in range(0x110000):
        char = chr(point)
        if unicodedata.category(char) not in {"Cn", "Cs"}:
            assert core.fold(char) == fold(char), f"U+{point:04X}"
