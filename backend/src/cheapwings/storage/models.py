"""Persistence only. Money is decimal text; instants are UTC epoch milliseconds."""

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SearchJob(Base):
    __tablename__ = "search_jobs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    query_json: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String, default="queued", index=True)
    phase: Mapped[str] = mapped_column(String, default="searching")
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[int] = mapped_column(Integer)
    completed_at: Mapped[int | None] = mapped_column(Integer)
    deadline_at: Mapped[int] = mapped_column(Integer)
    data_expires_at: Mapped[int | None] = mapped_column(Integer)
    provider_ids: Mapped[list | None] = mapped_column(JSON)
    cache_mode: Mapped[str] = mapped_column(
        String, default="prefer_cache", server_default="prefer_cache"
    )
    upstream_work_reserved: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    reprice_budget: Mapped[int] = mapped_column(Integer, default=0)
    reprice_providers: Mapped[list] = mapped_column(JSON, default=list)
    verification_planned: Mapped[bool] = mapped_column(Boolean, default=False)


class WorkItem(Base):
    __tablename__ = "work_items"
    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "provider_id",
            "origin",
            "destination",
            "departure_date",
            "work_type",
            "target_key",
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("search_jobs.id"), index=True)
    provider_id: Mapped[str] = mapped_column(String, index=True)
    origin: Mapped[str] = mapped_column(String)
    destination: Mapped[str] = mapped_column(String)
    departure_date: Mapped[str] = mapped_column(String)
    work_type: Mapped[str] = mapped_column(String, default="detailed")
    target_key: Mapped[str] = mapped_column(String, default="")
    status: Mapped[str] = mapped_column(String, index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[int] = mapped_column(Integer, default=0)
    leased_until: Mapped[int | None] = mapped_column(Integer)
    lease_token: Mapped[str | None] = mapped_column(String)
    last_error_code: Mapped[str | None] = mapped_column(String)
    last_error_detail: Mapped[str | None] = mapped_column(Text)
    operation_id: Mapped[str | None] = mapped_column(
        ForeignKey("provider_operations.id"), index=True
    )
    result_origin: Mapped[str] = mapped_column(String, default="live", server_default="live")
    observation_retrieved_at: Mapped[int | None] = mapped_column(Integer)
    reused_at: Mapped[int | None] = mapped_column(Integer)
    cache_fresh_until: Mapped[int | None] = mapped_column(Integer)
    provider_complete: Mapped[bool | None] = mapped_column(Boolean)
    result_count: Mapped[int | None] = mapped_column(Integer)
    unpriced_candidate_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[int | None] = mapped_column(Integer)
    finished_at: Mapped[int | None] = mapped_column(Integer)


class WorkAttempt(Base):
    __tablename__ = "work_attempts"
    __table_args__ = (UniqueConstraint("work_item_id", "attempt"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    work_item_id: Mapped[str] = mapped_column(ForeignKey("work_items.id"), index=True)
    attempt: Mapped[int] = mapped_column(Integer)
    started_at: Mapped[int] = mapped_column(Integer)
    finished_at: Mapped[int | None] = mapped_column(Integer)
    outcome: Mapped[str] = mapped_column(String, default="running")
    error_code: Mapped[str | None] = mapped_column(String)


class ItineraryRow(Base):
    __tablename__ = "itineraries"
    __table_args__ = (UniqueConstraint("job_id", "fingerprint"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("search_jobs.id"), index=True)
    fingerprint: Mapped[str | None] = mapped_column(String)
    identity_confidence: Mapped[str] = mapped_column(String)
    summary_json: Mapped[dict | None] = mapped_column(JSON)
    airport_transfers_json: Mapped[list | None] = mapped_column(JSON)


class SegmentRow(Base):
    __tablename__ = "segments"
    __table_args__ = (UniqueConstraint("itinerary_id", "ordinal"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    itinerary_id: Mapped[str] = mapped_column(ForeignKey("itineraries.id"), index=True)
    ordinal: Mapped[int] = mapped_column(Integer)
    canonical_json: Mapped[dict] = mapped_column(JSON)


class FXRow(Base):
    __tablename__ = "fx_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    base: Mapped[str] = mapped_column(String)
    quote: Mapped[str] = mapped_column(String)
    rate_decimal_text: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String)
    observed_at: Mapped[int] = mapped_column(Integer)


class FareQuote(Base):
    __tablename__ = "fare_quotes"
    __table_args__ = (UniqueConstraint("job_id", "provider_id", "source_quote_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("search_jobs.id"), index=True)
    itinerary_id: Mapped[str] = mapped_column(ForeignKey("itineraries.id"), index=True)
    provider_id: Mapped[str] = mapped_column(String)
    source_quote_id: Mapped[str] = mapped_column(String)
    raw_amount_decimal_text: Mapped[str] = mapped_column(Text)
    raw_currency: Mapped[str] = mapped_column(String)
    comparable_amount_decimal_text: Mapped[str | None] = mapped_column(Text)
    comparable_currency: Mapped[str | None] = mapped_column(String)
    canonical_json: Mapped[dict] = mapped_column(JSON)
    provider_quote_handle_server_side: Mapped[str | None] = mapped_column(Text)
    work_item_id: Mapped[str | None] = mapped_column(ForeignKey("work_items.id"), index=True)
    fx_snapshot_id: Mapped[int | None] = mapped_column(ForeignKey("fx_snapshots.id"))


class QuoteRevision(Base):
    __tablename__ = "quote_revisions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quote_id: Mapped[int] = mapped_column(ForeignKey("fare_quotes.id"), index=True)
    revision_time: Mapped[int] = mapped_column(Integer)
    amount_decimal_text: Mapped[str] = mapped_column(Text)
    currency: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(String)
    canonical_json: Mapped[dict | None] = mapped_column(JSON)


class ProviderState(Base):
    __tablename__ = "provider_state"
    provider_id: Mapped[str] = mapped_column(String, primary_key=True)
    next_request_at: Mapped[int] = mapped_column(Integer, default=0)


class ProviderOperation(Base):
    """A durable fetch independent of any subscriber's cancellation state."""

    __tablename__ = "provider_operations"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    cache_key: Mapped[str] = mapped_column(Text, index=True)
    provider_id: Mapped[str] = mapped_column(String, index=True)
    query_json: Mapped[dict] = mapped_column(JSON)
    origin: Mapped[str] = mapped_column(String)
    destination: Mapped[str] = mapped_column(String)
    departure_date: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[int] = mapped_column(Integer)
    deadline_at: Mapped[int] = mapped_column(Integer)
    hard_expires_at: Mapped[int] = mapped_column(Integer)
    next_attempt_at: Mapped[int] = mapped_column(Integer, default=0)
    leased_until: Mapped[int | None] = mapped_column(Integer)
    lease_token: Mapped[str | None] = mapped_column(String)
    primary_work_item_id: Mapped[str] = mapped_column(String)
    error_code: Mapped[str | None] = mapped_column(String)
    cache_ttl_seconds: Mapped[int] = mapped_column(Integer)

    @property
    def work_type(self):
        return "detailed"

    @property
    def job_id(self):
        return "shared_fetch"


class OperationAttempt(Base):
    __tablename__ = "operation_attempts"
    __table_args__ = (UniqueConstraint("operation_id", "attempt"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    operation_id: Mapped[str] = mapped_column(ForeignKey("provider_operations.id"), index=True)
    attempt: Mapped[int] = mapped_column(Integer)
    started_at: Mapped[int] = mapped_column(Integer)
    finished_at: Mapped[int | None] = mapped_column(Integer)
    outcome: Mapped[str] = mapped_column(String, default="running")


class ProviderResultCache(Base):
    __tablename__ = "provider_result_cache"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    cache_key: Mapped[str] = mapped_column(Text, index=True)
    provider_id: Mapped[str] = mapped_column(String, index=True)
    payload_json: Mapped[str] = mapped_column(Text)
    retrieved_at: Mapped[int] = mapped_column(Integer)
    cached_at: Mapped[int] = mapped_column(Integer)
    fresh_until: Mapped[int] = mapped_column(Integer, index=True)
    hard_expires_at: Mapped[int] = mapped_column(Integer)
    byte_size: Mapped[int] = mapped_column(Integer)
