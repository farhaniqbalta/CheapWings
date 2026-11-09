"""Canonical source evidence; no provider payloads, credentials or selectors."""
from dataclasses import dataclass
from datetime import datetime

from cheapwings.domain.money import FXSnapshot


@dataclass(frozen=True, slots=True)
class SourceEvidence:
    source_checked_at: datetime | None = None
    fx_snapshot: FXSnapshot | None = None
    fee_completeness: str = 'unknown'
    point_of_sale_country: str | None = None
    attribution: str | None = None


@dataclass
class ProviderFailure(Exception):
    code: str
    retry_after_seconds: float = 0
