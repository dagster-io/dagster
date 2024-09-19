"""add backfill table.

Revision ID: a914fb6ccdf9
Revises: 0da417ae1b81
Create Date: 2021-02-10 14:58:02.954242

"""

from dagster._core.storage.migration.utils import create_bulk_actions_table

# revision identifiers, used by Alembic.
revision = "a914fb6ccdf9"
down_revision = "0da417ae1b81"
branch_labels = None
depends_on = None


def upgrade():
    create_bulk_actions_table()


def downgrade():
    pass
