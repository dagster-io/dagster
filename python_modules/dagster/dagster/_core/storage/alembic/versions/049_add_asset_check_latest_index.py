"""Add an index for the latest asset check execution lookup.

Revision ID: b97a0c71e41d
Revises: 29b539ebc72a
"""

from alembic import op
from dagster._core.storage.migration.utils import has_index, has_table

revision = "b97a0c71e41d"
down_revision = "29b539ebc72a"
branch_labels = None
depends_on = None

TABLE_NAME = "asset_check_executions"
INDEX_NAME = "idx_asset_check_executions_latest"


def upgrade():
    if has_table(TABLE_NAME) and not has_index(TABLE_NAME, INDEX_NAME):
        op.create_index(
            INDEX_NAME,
            TABLE_NAME,
            ["asset_key", "check_name", "id"],
            mysql_length={"asset_key": 64, "check_name": 64},
        )


def downgrade():
    if has_table(TABLE_NAME) and has_index(TABLE_NAME, INDEX_NAME):
        op.drop_index(INDEX_NAME, TABLE_NAME)
