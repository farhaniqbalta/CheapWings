"""Offers: a price from a given provider+seller for a specific itinerary and fare product.

One itinerary can have many offers across providers/sellers/fare classes.
Never collapse them; never let `unknown` silently become `false`/`0`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from cheapwings.domain.money import Money


class ThreeValued(str, Enum):
    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"


class PriceStatus(str, Enum):
    REPRICED_EXACT = "repriced_exact"
    RECENT_SEARCH = "recent_search"
    INDICATIVE = "indicative"
    CHANGED_OR_UNAVAILABLE = "changed_or_unavailable"


class ComparisonStatus(str, Enum):
    ELIGIBLE_TOTAL_KNOWN = "eligible_total_known"
    EXTRA_COST_UNKNOWN = "extra_cost_unknown"
    MISSING_REQUIRED_BAGGAGE = "missing_required_baggage"
    INELIGIBLE = "ineligible"
    CURRENCY_UNRESOLVED = "currency_unresolved"


class LinkScope(str, Enum):
    EXACT_OFFER = "exact_offer"
    ITINERARY = "itinerary"
    GENERIC_SEARCH = "generic_search"
    UNAVAILABLE = "unavailable"


class ProviderErrorCode(str, Enum):
    NETWORK_TIMEOUT = "network_timeout"
    HTTP_RATE_LIMITED = "http_rate_limited"
    AUTH_DENIED = "auth_denied"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    SCHEMA_CHANGED = "schema_changed"
    PARTIAL_PAYLOAD = "partial_payload"
    INVALID_CURRENCY = "invalid_currency"
    INVALID_PRICE = "invalid_price"
    MISSING_SEGMENTS = "missing_segments"
    UNSAFE_FARE = "unsafe_fare"
    UNSUPPORTED_QUERY = "unsupported_query"
    TERMS_NOT_APPROVED = "terms_not_approved"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Offer:
    """A single seller/fare quote for one itinerary."""

    quote_id: str
    itinerary_id: str
    provider_id: str
    seller: str | None
    fare_family: str | None
    cabin: str
    basic_economy: bool

    amount_original: Money
    comparable_amount: Money | None
    comparison_status: ComparisonStatus

    checked_bag: ThreeValued
    hidden_city: ThreeValued
    self_transfer: ThreeValued

    price_status: PriceStatus
    is_estimate: bool

    retrieved_at: datetime
    repriced_at: datetime | None

    link: str | None
    link_scope: LinkScope

    provider_quote_handle: str | None  # opaque, server-only; never serialize to clients
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.price_status == PriceStatus.REPRICED_EXACT and self.is_estimate:
            raise ValueError(
                f"Offer {self.quote_id}: price_status=repriced_exact cannot coexist with "
                "is_estimate=True"
            )
        if self.hidden_city != ThreeValued.NO and self.price_status == PriceStatus.REPRICED_EXACT:
            # Hidden-city/unknown offers must never reach the safe-ranked repriced tier.
            raise ValueError(
                f"Offer {self.quote_id}: hidden_city={self.hidden_city.value} cannot be "
                "ranked in the safe repriced_exact tier"
            )
