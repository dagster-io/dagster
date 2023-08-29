"""Add asset check executions status index

Revision ID: 7dbe52b865b6
Revises: ec80dd91891a
Create Date: 2023-08-28 23:33:23.532049

"""
from alembic import op
from dagster._core.storage.migration.utils import has_index

# revision identifiers, used by Alembic.
revision = "7dbe52b865b6"
down_revision = "ec80dd91891a"
branch_labels = None
depends_on = None

TABLE_NAME = "asset_check_executions"
INDEX_NAME = "idx_asset_check_executions_status"


def upgrade():
    if not has_index(TABLE_NAME, INDEX_NAME):
        op.create_index(
            INDEX_NAME,
            TABLE_NAME,
            [
                "asset_key",
                "check_name",
                "execution_status",
            ],
            mysql_length={"asset_key": 64, "check_name": 64},
        )


def downgrade():
    if has_index(TABLE_NAME, INDEX_NAME):
        op.drop_index(INDEX_NAME, table_name=TABLE_NAME)
