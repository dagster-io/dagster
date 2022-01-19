"""add column last_observation_timestamp

Revision ID: 9642811d99b1
Revises: 05844c702676
Create Date: 2022-01-19 11:14:54.048737

"""
from dagster.core.storage.migration.utils import add_last_observation_timestamp_column

# revision identifiers, used by Alembic.
revision = '9642811d99b1'
down_revision = '05844c702676'
branch_labels = None
depends_on = None


def upgrade():
    add_last_observation_timestamp_column()


def downgrade():
    pass