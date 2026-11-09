"""Coverage ledger: tracks attempt/outcome per provider + route-date, separate from
completeness of flight inventory (which usually remains unknown)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum

from cheapwings.domain.offer import ProviderErrorCode


class WorkStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    RETRY_WAIT = "retry_wait"
    SUCCEEDED_RESULTS = "succeeded_results"
    SUCCEEDED_EMPTY = "succeeded_empty"
    FAILED_TERMINAL = "failed_terminal"
    SKIPPED_UNSUPPORTED = "skipped_unsupported"
    CANCELLED = "cancelled"


TERMINAL_STATUSES = frozenset(
    {
        WorkStatus.SUCCEEDED_RESULTS,
        WorkStatus.SUCCEEDED_EMPTY,
        WorkStatus.FAILED_TERMINAL,
        WorkStatus.SKIPPED_UNSUPPORTED,
        WorkStatus.CANCELLED,
    }
)


@dataclass(frozen=True, slots=True)
class CoverageEntry:
    """One provider's attempt at one route-date combination."""

    provider_id: str
    origin: str
    destination: str
    departure_date: date
    status: WorkStatus
    attempts: int
    error_code: ProviderErrorCode | None
    error_detail_sanitized: str | None
    result_count: int | None
    provider_complete: bool | None  # True/False/unknown(None): source said truncated or not
    started_at: datetime | None
    finished_at: datetime | None

    def __post_init__(self) -> None:
        if self.status == WorkStatus.SUCCEEDED_EMPTY and self.error_code is not None:
            raise ValueError("succeeded_empty must not carry an error_code")
        if self.status == WorkStatus.FAILED_TERMINAL and self.error_code is None:
            raise ValueError("failed_terminal requires an error_code; never collapse into empty")


def unique_covered_combinations(entries: list[CoverageEntry]) -> int:
    """Unique route-date keys with at least one successful provider response.

    Must never be derived by summing per-provider successes -- that double
    counts combinations covered by more than one provider.
    """
    covered = {
        (e.origin, e.destination, e.departure_date)
        for e in entries
        if e.status in (WorkStatus.SUCCEEDED_RESULTS, WorkStatus.SUCCEEDED_EMPTY)
    }
    return len(covered)
