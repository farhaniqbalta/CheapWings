from datetime import date

from cheapwings.domain.query import SearchQuery
from cheapwings.engine.expansion import expand_routes_and_dates


def _query(**overrides):
    defaults = dict(
        origins=["MEL"],
        destinations=["CGK", "DPS", "SUB"],
        departure_date_from=date(2026, 12, 12),
        departure_date_through=date(2026, 12, 20),
        display_currency="IDR",
    )
    defaults.update(overrides)
    return SearchQuery(**defaults)


def test_1x3x9_expands_to_27_combinations():
    query = _query()
    combos = expand_routes_and_dates(query)
    assert len(combos) == 27
    assert query.combination_count() == 27


def test_combos_are_unique_and_deterministic_order():
    combos = expand_routes_and_dates(_query())
    keys = [(c.origin, c.destination, c.departure_date) for c in combos]
    assert len(keys) == len(set(keys))
    assert keys[0] == ("MEL", "CGK", date(2026, 12, 12))
    assert keys[-1] == ("MEL", "SUB", date(2026, 12, 20))


def test_same_origin_destination_pair_is_skipped():
    query = _query(origins=["MEL", "DPS"], destinations=["DPS"])
    combos = expand_routes_and_dates(query)
    assert all(c.origin != c.destination for c in combos)
    # MEL->DPS over 9 days only (DPS->DPS skipped)
    assert len(combos) == 9


def test_duplicate_input_codes_are_deduplicated_before_expansion():
    query = _query(origins=["MEL", "mel"], destinations=["CGK"])
    assert query.origins == ["MEL"]
    combos = expand_routes_and_dates(query)
    assert len(combos) == 9
