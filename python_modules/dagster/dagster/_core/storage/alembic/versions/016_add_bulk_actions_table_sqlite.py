"""add backfill table

Revision ID: 6d366a41b4be
Revises: a914fb6ccdf9
Create Date: 2021-02-10 14:45:29.022887

"""
from dagster._core.storage.migration.utils import create_bulk_actions_table

# revision identifiers, used by Alembic.
revision = "6d366a41b4be"
down_revision = "a914fb6ccdf9"
branch_labels = None
depends_on = None

# pylint: disable=no-member


def upgrade():
    create_bulk_actions_table()


def downgrade():
    pass
