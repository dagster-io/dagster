"""add asset check partition latest index

Revision ID: 5d7426c3e7f2
Revises: 29b539ebc72a
Create Date: 2026-03-18 11:45:00.000000

"""

from alembic import op
from dagster._core.storage.migration.utils import has_index, has_table

# revision identifiers, used by Alembic.
revision = "5d7426c3e7f2"
down_revision = "29b539ebc72a"
branch_labels = None
depends_on = None

TABLE_NAME = "asset_check_executions"
INDEX_NAME = "idx_asset_check_executions_partition_latest"


def upgrade():
    if has_table(TABLE_NAME) and not has_index(TABLE_NAME, INDEX_NAME):
        op.create_index(
            INDEX_NAME,
            TABLE_NAME,
            ["asset_key", "check_name", "partition", "id"],
            mysql_length={"asset_key": 64, "partition": 64, "check_name": 64},
        )


def downgrade():
    if has_table(TABLE_NAME) and has_index(TABLE_NAME, INDEX_NAME):
        op.drop_index(INDEX_NAME, TABLE_NAME)
