"""Source evidence, partial itinerary identity and durable repricing.

SQLite supports a nullable inline REFERENCES column without rebuilding tables
that existing quote revisions reference. Defaults preserve populated P2 databases.
"""
from alembic import op
import sqlalchemy as sa

revision = '1cf9a06e0e54'
down_revision = 'e1f3a1193315'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('ALTER TABLE fare_quotes ADD COLUMN work_item_id VARCHAR REFERENCES work_items(id)')
    op.create_index('ix_fare_quotes_work_item_id', 'fare_quotes', ['work_item_id'])
    op.add_column('itineraries', sa.Column('summary_json', sa.JSON(), nullable=True))
    op.add_column('quote_revisions', sa.Column('canonical_json', sa.JSON(), nullable=True))
    op.execute('UPDATE quote_revisions SET canonical_json = '
               '(SELECT canonical_json FROM fare_quotes WHERE fare_quotes.id = quote_revisions.quote_id)')
    op.add_column('search_jobs', sa.Column('data_expires_at', sa.Integer(), nullable=True))
    op.add_column('search_jobs', sa.Column('reprice_budget', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('search_jobs', sa.Column('reprice_providers', sa.JSON(), nullable=False, server_default='[]'))
    op.add_column('search_jobs', sa.Column('verification_planned', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('work_items', sa.Column('unpriced_candidate_count', sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    op.drop_column('work_items', 'unpriced_candidate_count')
    op.drop_column('search_jobs', 'verification_planned')
    op.drop_column('search_jobs', 'reprice_providers')
    op.drop_column('search_jobs', 'reprice_budget')
    op.drop_column('search_jobs', 'data_expires_at')
    op.drop_column('quote_revisions', 'canonical_json')
    op.drop_column('itineraries', 'summary_json')
    op.drop_index('ix_fare_quotes_work_item_id', table_name='fare_quotes')
    op.drop_column('fare_quotes', 'work_item_id')
