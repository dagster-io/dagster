"""add range index

Revision ID: b37316bf5584
Revises: f4eed4c26e2c
Create Date: 2022-01-20 11:39:54.203976

"""
from dagster.core.storage.migration.utils import create_run_range_indices

# revision identifiers, used by Alembic.
revision = "b37316bf5584"
down_revision = "f4eed4c26e2c"
branch_labels = None
depends_on = None


def upgrade():
    create_run_range_indices()


def downgrade():
    pass
