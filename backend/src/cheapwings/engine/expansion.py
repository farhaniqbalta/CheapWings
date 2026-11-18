"""Pure route x date expansion. No I/O, no provider knowledge."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import cheapwings_core as _core

from cheapwings.domain.query import SearchQuery


@dataclass(frozen=True, slots=True)
class RouteDateCombo:
    origin: str
    destination: str
    departure_date: date


def expand_routes_and_dates(query: SearchQuery) -> list[RouteDateCombo]:
    """Expand every valid origin x destination x inclusive-date combination.

    Skips same-origin-destination pairs. Does not deduplicate beyond what
    SearchQuery already normalized (unique origins/destinations). Order is
    deterministic: origin, then destination, then date.
    """
    return [
        RouteDateCombo(origin, destination, date.fromisoformat(departure))
        for origin, destination, departure in _core.plan_search(
            query.origins,
            query.destinations,
            query.departure_date_from.isoformat(),
            query.departure_date_through.isoformat(),
            query.max_combinations,
        )
    ]
