"""add backfill table

Revision ID: a914fb6ccdf9
Revises: 4ea2b1f6f67b
Create Date: 2021-02-10 14:58:02.954242

"""
from dagster.core.storage.migration.utils import create_bulk_actions_table

# revision identifiers, used by Alembic.
revision = "a914fb6ccdf9"
down_revision = "4ea2b1f6f67b"
branch_labels = None
depends_on = None

# pylint: disable=no-member


def upgrade():
    create_bulk_actions_table()


def downgrade():
    pass
