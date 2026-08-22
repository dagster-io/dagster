"""Add asset_event_idempotency_keys table.

Revision ID: 7bbdc9f35264
Revises: 29b539ebc72a
Create Date: 2026-08-14 00:00:00.000000

"""

import sqlalchemy as db
from alembic import op
from dagster._core.storage.migration.utils import has_index, has_table
from dagster._core.storage.sql import MySQLCompatabilityTypes, get_sql_current_timestamp
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = "7bbdc9f35264"
down_revision = "29b539ebc72a"
branch_labels = None
depends_on = None

TABLE_NAME = "asset_event_idempotency_keys"
UNIQUE_INDEX_NAME = "idx_asset_event_idempotency_keys_unique"


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
            db.Column("asset_key", MySQLCompatabilityTypes.UniqueText, nullable=False),
            db.Column("idempotency_key", MySQLCompatabilityTypes.UniqueText, nullable=False),
            db.Column("create_timestamp", db.DateTime, server_default=get_sql_current_timestamp()),
            db.Column(
                "is_confirmed", db.Boolean, nullable=False, default=False, server_default=db.false()
            ),
        )

    if not has_index(TABLE_NAME, UNIQUE_INDEX_NAME):
        op.create_index(
            UNIQUE_INDEX_NAME,
            TABLE_NAME,
            ["asset_key", "idempotency_key"],
            unique=True,
            mysql_length={"asset_key": 64, "idempotency_key": 64},
        )


def downgrade():
    if has_table(TABLE_NAME):
        if has_index(TABLE_NAME, UNIQUE_INDEX_NAME):
            op.drop_index(UNIQUE_INDEX_NAME, TABLE_NAME)

        op.drop_table(TABLE_NAME)
