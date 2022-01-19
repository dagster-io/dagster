"""add column last_observation_timestamp

Revision ID: 06bd7b15ca19
Revises: 29a8e9d74220
Create Date: 2022-01-18 21:22:49.337802

"""
from dagster.core.storage.migration.utils import add_last_observation_timestamp_column


# revision identifiers, used by Alembic.
revision = '06bd7b15ca19'
down_revision = '29a8e9d74220'
branch_labels = None
depends_on = None


def upgrade():
    add_last_observation_timestamp_column()


def downgrade():
    pass
