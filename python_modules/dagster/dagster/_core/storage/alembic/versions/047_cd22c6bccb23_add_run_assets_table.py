"""add run assets table

Revision ID: cd22c6bccb23
Revises: 16e3655b4d9b
Create Date: 2024-10-27 15:23:05.700683

"""

import sqlalchemy as db
from alembic import op
from dagster._core.storage.migration.utils import has_index, has_table
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = "cd22c6bccb23"
down_revision = "16e3655b4d9b"
branch_labels = None
depends_on = None


TABLE_NAME = "run_assets"
INDEX_NAME = "idx_run_assets"
UNIQUE_INDEX_NAME = "idx_run_assets_unique"


def upgrade():
    if not has_table(TABLE_NAME):
        op.create_table(
            TABLE_NAME,
            db.Column(
                "id",
                db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
                primary_key=True,
                autoincrement=True,
            ),
            db.Column("run_id", db.String(255), db.ForeignKey("runs.run_id", ondelete="CASCADE")),
            db.Column("asset_key", db.Text),
        )

    if not has_index(TABLE_NAME, INDEX_NAME):
        op.create_index(
            INDEX_NAME,
            TABLE_NAME,
            [
                "run_id",
                "asset_key",
            ],
            mysql_length={"run_id": 255, "asset_key": 64},
        )

    if not has_index(TABLE_NAME, UNIQUE_INDEX_NAME):
        op.create_index(
            UNIQUE_INDEX_NAME,
            TABLE_NAME,
            [
                "run_id",
                "asset_key",
            ],
            unique=True,
            mysql_length={"run_id": 255, "asset_key": 64},
        )


def downgrade():
    if has_table(TABLE_NAME):
        if has_index(TABLE_NAME, UNIQUE_INDEX_NAME):
            op.drop_index(UNIQUE_INDEX_NAME, TABLE_NAME)

        if has_index(TABLE_NAME, INDEX_NAME):
            op.drop_index(INDEX_NAME, TABLE_NAME)

        op.drop_table(TABLE_NAME)
