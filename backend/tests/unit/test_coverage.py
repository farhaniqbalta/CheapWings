from datetime import date

import pytest

from cheapwings.domain.coverage import CoverageEntry, WorkStatus, unique_covered_combinations
from cheapwings.domain.offer import ProviderErrorCode


def _entry(provider_id, status, origin="MEL", destination="DPS", d=date(2026, 12, 16), error=None):
    return CoverageEntry(
        provider_id=provider_id,
        origin=origin,
        destination=destination,
        departure_date=d,
        status=status,
        attempts=1,
        error_code=error,
        error_detail_sanitized=None,
        result_count=None,
        provider_complete=True,
        started_at=None,
        finished_at=None,
    )


def test_unique_covered_combinations_does_not_double_count_providers():
    entries = [
        _entry("skiplagged", WorkStatus.SUCCEEDED_RESULTS),
        _entry("swoop", WorkStatus.SUCCEEDED_RESULTS),  # same route-date, different provider
    ]
    assert unique_covered_combinations(entries) == 1


def test_failed_terminal_requires_error_code():
    with pytest.raises(ValueError):
        _entry("skiplagged", WorkStatus.FAILED_TERMINAL, error=None)


def test_succeeded_empty_cannot_carry_error_code():
    with pytest.raises(ValueError):
        _entry("skiplagged", WorkStatus.SUCCEEDED_EMPTY, error=ProviderErrorCode.UNKNOWN)


def test_failure_is_not_counted_as_covered():
    entries = [_entry("skiplagged", WorkStatus.FAILED_TERMINAL, error=ProviderErrorCode.NETWORK_TIMEOUT)]
    assert unique_covered_combinations(entries) == 0
