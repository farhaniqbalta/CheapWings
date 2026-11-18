"""UI/provider-independent scope arithmetic. Same-airport pairs never become work."""

from collections.abc import Sequence
from datetime import date

import cheapwings_core as _core


def plan_scope(
    origins: list[str],
    destinations: list[str],
    start: date,
    end: date,
    provider_ids: Sequence[str] = (),
) -> dict:
    values = _core.plan_scope(
        origins, destinations, start.isoformat(), end.isoformat(), list(provider_ids)
    )
    return dict(
        zip(
            ("date_count", "valid_pairs", "combinations", "provider_count", "estimated_work_items"),
            values,
        )
    )
