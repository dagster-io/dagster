"""add asset_check_executions table

Revision ID: ec80dd91891a
Revises: 5771160a95ad
Create Date: 2023-08-21 12:05:47.817280

"""
import sqlalchemy as db
from alembic import op
from dagster._core.storage.migration.utils import has_index, has_table
from dagster._core.storage.sql import get_current_timestamp
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = "ec80dd91891a"
down_revision = "5771160a95ad"
branch_labels = None
depends_on = None

TABLE_NAME = "asset_check_executions"
INDEX_NAME = "idx_asset_check_executions"
UNIQUE_INDEX_NAME = "idx_asset_check_executions_unique"


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
            db.Column("asset_key", db.Text),
            db.Column("check_name", db.Text),
            db.Column(
                "partition", db.Text
            ),  # Currently unused. Planned for future partition support
            db.Column("run_id", db.String(255)),
            db.Column("execution_status", db.String(255)),  # Planned, Success, or Failure
            db.Column("evaluation_event", db.Text),
            db.Column("evaluation_event_timestamp", db.DateTime),
            db.Column(
                "evaluation_event_storage_id",
                db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
            ),
            db.Column(
                "materialization_event_storage_id",
                db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
            ),
            db.Column("create_timestamp", db.DateTime, server_default=get_current_timestamp()),
        )

    if not has_index(TABLE_NAME, INDEX_NAME):
        op.create_index(
            INDEX_NAME,
            TABLE_NAME,
            [
                "asset_key",
                "check_name",
                "materialization_event_storage_id",
                "partition",
            ],
            mysql_length={"asset_key": 64, "partition": 64, "check_name": 64},
        )

    if not has_index(TABLE_NAME, UNIQUE_INDEX_NAME):
        op.create_index(
            UNIQUE_INDEX_NAME,
            TABLE_NAME,
            [
                "asset_key",
                "check_name",
                "run_id",
                "partition",
            ],
            unique=True,
            mysql_length={"asset_key": 64, "partition": 64, "check_name": 64},
        )


def downgrade():
    if has_table(TABLE_NAME):
        if has_index(TABLE_NAME, UNIQUE_INDEX_NAME):
            op.drop_index(UNIQUE_INDEX_NAME, TABLE_NAME)

        if has_index(TABLE_NAME, INDEX_NAME):
            op.drop_index(INDEX_NAME, TABLE_NAME)

        op.drop_table(TABLE_NAME)
