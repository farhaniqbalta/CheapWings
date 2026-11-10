"""Bounded observation cache and independent coalesced provider operations."""

import sqlalchemy as sa
from alembic import op

revision = "8d103ce214ab"
down_revision = "7a2c9e103f41"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "provider_operations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("cache_key", sa.Text(), nullable=False),
        sa.Column("provider_id", sa.String(), nullable=False),
        sa.Column("query_json", sa.JSON(), nullable=False),
        sa.Column("origin", sa.String(), nullable=False),
        sa.Column("destination", sa.String(), nullable=False),
        sa.Column("departure_date", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.Integer(), nullable=False),
        sa.Column("deadline_at", sa.Integer(), nullable=False),
        sa.Column("hard_expires_at", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.Integer(), nullable=False),
        sa.Column("leased_until", sa.Integer()),
        sa.Column("lease_token", sa.String()),
        sa.Column("primary_work_item_id", sa.String(), nullable=False),
        sa.Column("error_code", sa.String()),
        sa.Column("cache_ttl_seconds", sa.Integer(), nullable=False),
    )
    for col in ("cache_key", "provider_id", "status"):
        op.create_index(f"ix_provider_operations_{col}", "provider_operations", [col])
    op.create_table(
        "operation_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "operation_id", sa.String(), sa.ForeignKey("provider_operations.id"), nullable=False
        ),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.Integer(), nullable=False),
        sa.Column("finished_at", sa.Integer()),
        sa.Column("outcome", sa.String(), nullable=False),
        sa.UniqueConstraint("operation_id", "attempt"),
    )
    op.create_index("ix_operation_attempts_operation_id", "operation_attempts", ["operation_id"])
    op.create_table(
        "provider_result_cache",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("cache_key", sa.Text(), nullable=False),
        sa.Column("provider_id", sa.String(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("retrieved_at", sa.Integer(), nullable=False),
        sa.Column("cached_at", sa.Integer(), nullable=False),
        sa.Column("fresh_until", sa.Integer(), nullable=False),
        sa.Column("hard_expires_at", sa.Integer(), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
    )
    for col in ("cache_key", "provider_id", "fresh_until"):
        op.create_index(f"ix_provider_result_cache_{col}", "provider_result_cache", [col])
    op.add_column("search_jobs", sa.Column("provider_ids", sa.JSON()))
    op.add_column(
        "search_jobs",
        sa.Column("cache_mode", sa.String(), nullable=False, server_default="prefer_cache"),
    )
    op.add_column(
        "search_jobs",
        sa.Column("upstream_work_reserved", sa.Boolean(), nullable=False, server_default="1"),
    )
    # Direct nullable inline FK addition avoids rebuilding a table referenced by
    # historical work_attempts/fare_quotes with PRAGMA foreign_keys=ON.
    op.execute(
        "ALTER TABLE work_items ADD COLUMN operation_id VARCHAR CONSTRAINT fk_work_operation REFERENCES provider_operations(id)"
    )
    op.add_column(
        "work_items", sa.Column("result_origin", sa.String(), nullable=False, server_default="live")
    )
    for col in ("observation_retrieved_at", "reused_at", "cache_fresh_until"):
        op.add_column("work_items", sa.Column(col, sa.Integer()))
    op.create_index("ix_work_items_operation_id", "work_items", ["operation_id"])


def downgrade():
    op.drop_index("ix_work_items_operation_id", table_name="work_items")
    for col in (
        "cache_fresh_until",
        "reused_at",
        "observation_retrieved_at",
        "result_origin",
        "operation_id",
    ):
        op.drop_column("work_items", col)
    for col in ("upstream_work_reserved", "cache_mode", "provider_ids"):
        op.drop_column("search_jobs", col)
    op.drop_table("provider_result_cache")
    op.drop_table("operation_attempts")
    op.drop_table("provider_operations")
