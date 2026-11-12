"""Public v1 contract. Provider selectors/raw payloads have no public DTO field."""

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from cheapwings.domain.coverage import WorkStatus
from cheapwings.domain.itinerary import IdentityConfidence
from cheapwings.domain.offer import (
    ComparisonStatus,
    LinkScope,
    PriceStatus,
    ProviderErrorCode,
    ThreeValued,
)
from cheapwings.domain.query import MaxStops, SearchQuery
from cheapwings.locations.catalog import MajorSelection, catalog

JobStatus = Literal["queued", "running", "completed", "partial", "failed", "cancelled"]
Sort = Literal["best_checked", "lowest_advertised"]


class DTO(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Passengers(DTO):
    adults: Literal[1] = 1


class SearchRequest(DTO):
    origin_selection: MajorSelection | None = None
    destination_selection: MajorSelection | None = None
    provider_ids: list[str] | None = Field(default=None, min_length=1, max_length=10)
    cache_mode: Literal["prefer_cache", "refresh"] = "prefer_cache"
    trip_type: Literal["one_way"] = "one_way"
    origins: list[Annotated[str, Field(max_length=16)]] = Field(min_length=1, max_length=120)
    destinations: list[Annotated[str, Field(max_length=16)]] = Field(min_length=1, max_length=120)
    departure_date_from: date
    departure_date_through: date
    passengers: Passengers = Field(default_factory=Passengers)
    cabin: Literal["economy"] = "economy"
    include_basic_economy: bool = True
    max_stops: Literal[0, 1, 2] | None = None
    checked_bags_required: bool = False
    display_currency: Literal["IDR", "USD", "AUD", "JPY"] = "IDR"
    point_of_sale_country: str | None = Field(default=None, pattern="^[A-Z]{2}$")
    include_hidden_city: bool = False

    def to_domain(self, cap):
        if self.departure_date_from < date.today():
            raise ValueError("Departure window has expired; choose today or a future date")
        metro_codes = {
            c.strip().upper() for c in self.origins + self.destinations
        } & catalog().metro_only_codes
        if metro_codes:
            raise ValueError(
                f"Metropolitan codes {', '.join(sorted(metro_codes))} are city locations; "
                "choose physical airport codes or a typed Major selection"
            )
        for selection, codes in (
            (self.origin_selection, self.origins),
            (self.destination_selection, self.destinations),
        ):
            if selection is not None:
                resolved = catalog().resolve(selection)
                if sorted({c.strip().upper() for c in codes}) != resolved.codes:
                    raise ValueError("Major selection must match the complete curated airport list")
        data = self.model_dump(exclude={"passengers", "max_stops", "provider_ids", "cache_mode"})
        return SearchQuery(
            **data,
            adults=self.passengers.adults,
            max_stops=MaxStops.ANY if self.max_stops is None else MaxStops(str(self.max_stops)),
            max_combinations=cap,
        )


class Created(DTO):
    job_id: str
    status: JobStatus
    created_at: datetime
    total_route_date_combinations: int
    enabled_detailed_providers: list[str]
    job_status_url: str


class ProviderCapability(DTO):
    provider_id: str
    enabled: bool
    disabled_reason: str | None
    detailed_search: bool
    calendar: bool
    exact_reprice: bool
    has_booking_link: bool
    has_hidden_city_flag: bool
    has_baggage_details: bool
    permitted_to_aggregate: bool = True
    can_cache: bool = True
    attribution_required: bool = False
    retention_seconds: int | None = None
    usage_policy_reviewed_on: str | None = None
    default_selected: bool = True  # pre-checked in the web source picker


class Capabilities(DTO):
    search_cache_enabled: bool = False
    search_cache_ttl_seconds: int = 1200
    max_hourly_requests: int = 100
    providers: list[ProviderCapability]
    supported_currencies: list[str]
    max_route_date_combinations: int
    max_active_jobs: int
    max_hourly_jobs: int
    synthetic_mode: bool
    inventory_completeness: Literal["unknown"] = "unknown"


class PoolProvider(DTO):
    provider_id: str
    priority: int
    running: int
    wait_ms: int  # until the next start is allowed; 0 = ready
    cooling_down: bool  # wait exceeds normal pacing: 429/Retry-After cooldown


class WorkerPool(DTO):
    """Persisted view; threads still finishing after a timeout are not visible here."""

    global_capacity: int
    low_priority_headroom: int
    running: int
    providers: list[PoolProvider]


class Health(DTO):
    status: Literal["ok"] = "ok"
    service: Literal["cheapwings"] = "cheapwings"


class Coverage(DTO):
    result_origin: Literal["live", "cache", "shared_inflight"] = "live"
    observation_retrieved_at: datetime | None = None
    reused_at: datetime | None = None
    cache_fresh_until: datetime | None = None
    operation_attempts: int = 0
    work_item_id: str
    work_type: str = "detailed"
    unpriced_candidate_count: int = 0
    provider_id: str
    origin: str
    destination: str
    departure_date: date
    status: WorkStatus
    attempts: int
    error_code: ProviderErrorCode | None
    error_detail_sanitized: str | None
    result_count: int | None
    provider_complete: bool | None
    started_at: datetime | None
    finished_at: datetime | None


class ProviderProgress(DTO):
    provider_id: str
    succeeded: int
    pending: int = 0
    running: int = 0
    retry_wait: int = 0
    failed: int
    cancelled: int
    skipped_unsupported: int
    disabled_reason: str | None


class Job(DTO):
    provider_ids: list[str] = Field(default_factory=list)
    cache_mode: Literal["prefer_cache", "refresh"] = "prefer_cache"
    job_id: str
    query: SearchRequest
    status: JobStatus
    phase: Literal["searching", "verifying", "done"]
    cancel_requested: bool
    created_at: datetime
    updated_at: datetime
    total_route_date_combinations: int
    covered_route_date_combinations: int
    total_provider_work_items: int
    succeeded_provider_work_items: int
    succeeded_empty: int
    failed_provider_work_items: int
    skipped_unsupported: int
    cancelled_provider_work_items: int
    inventory_completeness: Literal["unknown"] = "unknown"
    exact_reprice_attempted: int = 0
    exact_reprice_succeeded: int = 0
    data_expires_at: datetime | None = None
    provider_status: list[ProviderProgress]
    coverage: list[Coverage]
    warnings: list[str]


class Segment(DTO):
    ordinal: int
    marketing_carrier: str
    operating_carrier: str
    flight_number: str
    origin: str
    destination: str
    depart_at: datetime
    arrive_at: datetime
    marketing_carrier_name: str | None = None
    operating_carrier_name: str | None = None


class AirportTransfer(DTO):
    after_segment: int
    from_airport: str
    to_airport: str


class PublicOffer(DTO):
    expires_at: datetime | None = None
    result_origin: Literal["live", "cache", "shared_inflight"] = "live"
    reused_at: datetime | None = None
    quote_id: str
    provider_id: str
    seller: str | None
    fare_family: str | None
    cabin: str
    basic_economy: bool | None
    amount_original: str
    currency_original: str
    comparable_amount: str | None
    comparable_currency: str | None
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
    fee_completeness: str = "unknown"
    source_checked_at: datetime | None = None
    point_of_sale_country: str | None = None
    attribution: str | None = None
    fx_rate: str | None = None
    fx_as_of: str | None = None
    warnings: list[str]


class PublicItinerary(DTO):
    itinerary_id: str
    identity_confidence: IdentityConfidence
    origin: str
    destination: str
    departure_local: datetime
    arrival_local: datetime
    duration_minutes: int
    stops: int
    segments: list[Segment]
    carrier_names: list[str] = Field(default_factory=list)
    airport_transfers: list[AirportTransfer] = Field(default_factory=list)
    offers: list[PublicOffer]
    ranked_quote_id: str
    warnings: list[str] = Field(default_factory=list)


class ExpiredObservation(DTO):
    provider_id: str
    origin: str
    destination: str
    departure_date: date
    observed_at: datetime | None
    expired_at: datetime
    state: Literal["expired_details_unavailable"] = "expired_details_unavailable"


class Results(DTO):
    server_time: datetime | None = None
    expired_observations: list[ExpiredObservation] = Field(default_factory=list)
    next_expiry_at: datetime | None = None
    job_id: str
    status: JobStatus
    sort: Sort
    as_of: datetime
    next_cursor: str | None
    itineraries: list[PublicItinerary]
    warnings: list[str]
