"""add runtime partitions table

Revision ID: e62c379ac8f4
Revises: 6df03f4b1efb
Create Date: 2023-01-19 11:41:41.062228

"""
import sqlalchemy as db
from alembic import op
from dagster._core.storage.migration.utils import has_index, has_table
from dagster._core.storage.sql import get_current_timestamp
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = "e62c379ac8f4"
down_revision = "6df03f4b1efb"
branch_labels = None
depends_on = None


def upgrade():
    if not has_table("mutable_partitions"):
        op.create_table(
            "mutable_partitions",
            db.Column(
                "id",
                db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
                primary_key=True,
                autoincrement=True,
            ),
            db.Column("partitions_def_name", db.Text, nullable=False),
            db.Column("partition", db.Text, nullable=False),
            db.Column("create_timestamp", db.DateTime, server_default=get_current_timestamp()),
        )
        op.create_index(
            "idx_mutable_partitions",
            "mutable_partitions",
            ["partitions_def_name", "partition"],
            mysql_length={"partitions_def_name": 64, "partition": 64},
            unique=True,
        )


def downgrade():
    if has_index("mutable_partitions", "idx_mutable_partitions"):
        op.drop_index("idx_mutable_partition_keys", "mutable_partitions")

    if has_table("mutable_partitions"):
        op.drop_table("mutable_partitions")
