"""add concurrency limits table

Revision ID: 46b412388816
Revises: ec80dd91891a
Create Date: 2023-12-01 14:35:47.622154

"""

import sqlalchemy as db
from alembic import op
from dagster._core.storage.migration.utils import has_table
from dagster._core.storage.sql import MySQLCompatabilityTypes, get_sql_current_timestamp
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = "46b412388816"
down_revision = "ec80dd91891a"
branch_labels = None
depends_on = None


def upgrade():
    if not has_table("concurrency_limits"):
        op.create_table(
            "concurrency_limits",
            db.Column(
                "id",
                db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
                primary_key=True,
                autoincrement=True,
            ),
            db.Column(
                "concurrency_key", MySQLCompatabilityTypes.UniqueText, nullable=False, unique=True
            ),
            db.Column("limit", db.Integer, nullable=False),
            db.Column("update_timestamp", db.DateTime, server_default=get_sql_current_timestamp()),
            db.Column("create_timestamp", db.DateTime, server_default=get_sql_current_timestamp()),
        )


def downgrade():
    if has_table("concurrency_limits"):
        op.drop_table("concurrency_limits")
