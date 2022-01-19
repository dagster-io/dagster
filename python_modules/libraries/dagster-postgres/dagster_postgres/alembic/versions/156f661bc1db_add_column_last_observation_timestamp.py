"""add column last_observation_timestamp


Revision ID: 156f661bc1db
Revises: 42add02bf976
Create Date: 2022-01-18 21:04:06.192577

"""
from dagster.core.storage.migration.utils import add_last_observation_timestamp_column

# revision identifiers, used by Alembic.
revision = '156f661bc1db'
down_revision = '42add02bf976'
branch_labels = None
depends_on = None


def upgrade():
    add_last_observation_timestamp_column()


def downgrade():
    pass
