"""Pure route x date expansion. No I/O, no provider knowledge."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

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
    combos: list[RouteDateCombo] = []
    days = (query.departure_date_through - query.departure_date_from).days + 1
    for origin in query.origins:
        for destination in query.destinations:
            if origin == destination:
                continue
            for offset in range(days):
                departure = query.departure_date_from + timedelta(days=offset)
                combos.append(RouteDateCombo(origin, destination, departure))
    return combos
