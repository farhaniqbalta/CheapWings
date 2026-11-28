"""P7.4 Discover: job kind, discovery counts and the observation snapshot."""

import sqlalchemy as sa
from alembic import op

revision = "b7d3e91c2f40"
down_revision = "a49b10d15c01"
branch_labels = None
depends_on = None


def upgrade():
    # Plain ADD COLUMN: a batch rebuild of search_jobs would trip existing foreign keys.
    op.add_column("search_jobs", sa.Column("kind", sa.String(), nullable=False, server_default="search"))
    op.add_column("search_jobs", sa.Column("discovery_json", sa.JSON(), nullable=True))
    op.create_table(
        "discovery_observations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.String(), sa.ForeignKey("search_jobs.id"), nullable=False),
        sa.Column("work_item_id", sa.String(), sa.ForeignKey("work_items.id"), nullable=False),
        sa.Column("idx", sa.Integer(), nullable=False),
        sa.Column("observation_json", sa.JSON(), nullable=False),
        sa.Column("fx_json", sa.JSON(), nullable=False),
        sa.UniqueConstraint("work_item_id", "idx", name="uq_discovery_observation_item_idx"),
    )
    op.create_index("ix_discovery_observations_job_id", "discovery_observations", ["job_id"])


def downgrade():
    op.drop_index("ix_discovery_observations_job_id", table_name="discovery_observations")
    op.drop_table("discovery_observations")
    op.drop_column("search_jobs", "discovery_json")
    op.drop_column("search_jobs", "kind")
