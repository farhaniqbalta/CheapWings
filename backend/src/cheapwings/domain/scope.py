"""UI/provider-independent scope arithmetic. Same-airport pairs never become work."""

from collections.abc import Sequence
from datetime import date


def plan_scope(
    origins: list[str],
    destinations: list[str],
    start: date,
    end: date,
    provider_ids: Sequence[str] = (),
) -> dict:
    origins = list(dict.fromkeys(c.strip().upper() for c in origins))
    destinations = list(dict.fromkeys(c.strip().upper() for c in destinations))
    days = max(0, (end - start).days + 1)
    pairs = len(origins) * len(destinations) - len(set(origins) & set(destinations))
    combinations = pairs * days
    return {
        "date_count": days,
        "valid_pairs": pairs,
        "combinations": combinations,
        "provider_count": len(set(provider_ids)),
        "estimated_work_items": combinations * len(set(provider_ids)),
    }
