from copy import deepcopy
from datetime import date, timedelta

import pytest
from cheapwings.domain.query import SearchQuery
from cheapwings.domain.scope import plan_scope
from cheapwings.engine.expansion import expand_routes_and_dates
from cheapwings.locations.catalog import LocationCatalog, MajorSelection, catalog
from pydantic import ValidationError


def selection(id="country:JP", type="country", **kw):
    return MajorSelection(location_id=id, type=type, catalog_version=catalog().version, **kw)


@pytest.mark.parametrize(
    "text,code",
    [
        ("cgk", "CGK"),
        ("Haneda", "HND"),
        ("Narita", "NRT"),
        ("Tokyo", "HND"),
        ("Japan", "HND"),
        ("Bali", "DPS"),
        ("Soekarno Hatta", "CGK"),
        ("東京羽田", "HND"),
        ("Sao Paulo", "GRU"),
    ],
)
def test_lookup(text, code):
    matches = catalog().search(text)
    assert any(e.get("code") == code for e in matches)
    assert matches == catalog().search(text.upper())


def test_typed_metro_and_exact_airport():
    assert catalog().search("CGK")[0]["id"] == "airport:CGK"
    for code in ("JKT", "TYO", "LON"):
        matches = catalog().search(code)
        assert any(e["type"] == "city" and code in e["aliases"] for e in matches)
        assert code not in catalog().airports


def test_parent_browse_never_resolves_to_search_automatically():
    codes = [e["code"] for e in catalog().get_airports("metro:JP:TYO")]
    assert codes == ["HND", "NRT"]
    assert catalog().search("", "metro:JP:TYO") == catalog().search("", "metro:JP:TYO")
    assert all(e["type"] == "airport" for e in catalog().search("", "country:JP"))


def test_ambiguous_cities_keep_distinct_ids_and_geography():
    cities = [e for e in catalog().search("Springfield") if e["type"] == "city"]
    assert len(cities) > 1
    assert len({e["id"] for e in cities}) == len(cities)
    assert all(e.get("region") and e["country_name"] for e in cities)


def test_major_resolution_and_no_fallback():
    assert catalog().resolve(selection("metro:JP:TYO", "city")).codes == ["HND", "NRT"]
    assert catalog().resolve(selection()).codes == catalog().resolve(selection()).codes
    for value in (
        selection("country:US"),
        selection("bogus"),
        selection("country:JP", "city"),
        selection().model_copy(update={"catalog_version": "old"}),
    ):
        with pytest.raises(ValueError):
            catalog().resolve(value)
    with pytest.raises(ValidationError):
        MajorSelection(**{**selection().model_dump(), "coverage_mode": "all"})


@pytest.mark.parametrize("mutation", ["id", "code", "association", "mapping"])
def test_catalog_rejects_inconsistent_data(mutation):
    data = deepcopy(catalog().data)
    if mutation == "id":
        data["entities"].append(data["entities"][0])
    if mutation == "code":
        data["entities"].append({**data["entities"][0], "id": "airport:duplicate"})
    if mutation == "association":
        data["entities"][0]["codes"] = ["ZZZ"]
    if mutation == "mapping":
        data["major"]["country:JP"]["codes"] = ["CGK"]
    with pytest.raises(ValueError):
        LocationCatalog(data)


@pytest.mark.parametrize("days,valid", [(120, True), (121, False)])
def test_boundary_and_overlap_match_expansion(days, valid):
    start = date(2027, 1, 1)
    args = {
        "origins": ["MEL", "mel", "DPS"],
        "destinations": ["DPS"],
        "departure_date_from": start,
        "departure_date_through": start + timedelta(days=days - 1),
        "display_currency": "IDR",
        "max_combinations": 120,
    }
    if valid:
        query = SearchQuery(**args)
        assert query.combination_count() == len(expand_routes_and_dates(query)) == 120
    else:
        with pytest.raises(ValidationError, match="121"):
            SearchQuery(**args)
    plan = plan_scope(
        args["origins"],
        args["destinations"],
        start,
        args["departure_date_through"],
        ["a", "a", "b"],
    )
    assert plan["combinations"] == days
    assert plan["estimated_work_items"] == days * 2


def test_zero_routes_and_date_changes():
    assert plan_scope(["MEL"], ["MEL"], date(2027, 1, 1), date(2027, 1, 2))["combinations"] == 0
    with pytest.raises(ValidationError):
        SearchQuery(
            origins=["MEL"],
            destinations=["MEL"],
            departure_date_from=date(2027, 1, 1),
            departure_date_through=date(2027, 1, 1),
            display_currency="IDR",
        )
