"""Retain explicitly observed airport changes without inventing connecting flights."""

import sqlalchemy as sa
from alembic import op

revision = "7a2c9e103f41"
down_revision = "1cf9a06e0e54"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("itineraries", sa.Column("airport_transfers_json", sa.JSON(), nullable=True))


def downgrade():
    op.drop_column("itineraries", "airport_transfers_json")
