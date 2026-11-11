"""Persist fair job dispatch order without changing existing job deadlines."""

import sqlalchemy as sa
from alembic import op

revision = "a49b10d15c01"
down_revision = "91f4b02a671c"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "search_jobs",
        sa.Column("dispatch_sequence", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_search_jobs_dispatch_sequence", "search_jobs", ["dispatch_sequence"])


def downgrade():
    op.drop_index("ix_search_jobs_dispatch_sequence", table_name="search_jobs")
    op.drop_column("search_jobs", "dispatch_sequence")
