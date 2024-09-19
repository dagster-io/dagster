"""add dynamic partitions table

Revision ID: e62c379ac8f4
Revises: 16689497301f
Create Date: 2023-01-19 11:41:41.062228

"""

import sqlalchemy as db
from alembic import op
from dagster._core.storage.migration.utils import has_index, has_table
from dagster._core.storage.sql import get_sql_current_timestamp
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = "e62c379ac8f4"
down_revision = "16689497301f"
branch_labels = None
depends_on = None


def upgrade():
    if not has_table("dynamic_partitions"):
        op.create_table(
            "dynamic_partitions",
            db.Column(
                "id",
                db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
                primary_key=True,
                autoincrement=True,
            ),
            db.Column("partitions_def_name", db.Text, nullable=False),
            db.Column("partition", db.Text, nullable=False),
            db.Column("create_timestamp", db.DateTime, server_default=get_sql_current_timestamp()),
        )
        op.create_index(
            "idx_dynamic_partitions",
            "dynamic_partitions",
            ["partitions_def_name", "partition"],
            mysql_length={"partitions_def_name": 64, "partition": 64},
            unique=True,
        )


def downgrade():
    if has_index("dynamic_partitions", "idx_dynamic_partitions"):
        op.drop_index("idx_dynamic_partitions", "dynamic_partitions")

    if has_table("dynamic_partitions"):
        op.drop_table("dynamic_partitions")
