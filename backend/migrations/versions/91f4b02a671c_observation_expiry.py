"""Separate observation retention from job execution; preserve legacy cutoffs."""
import sqlalchemy as sa
from alembic import op
revision = "91f4b02a671c"
down_revision = "8d103ce214ab"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("work_items", sa.Column("data_expires_at", sa.Integer(), nullable=True))
    op.execute("UPDATE work_items SET data_expires_at = (SELECT data_expires_at FROM search_jobs WHERE search_jobs.id = work_items.job_id)")

def downgrade():
    op.drop_column("work_items", "data_expires_at")
