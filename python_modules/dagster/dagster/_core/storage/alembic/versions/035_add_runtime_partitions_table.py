"""add runtime partitions table

Revision ID: e62c379ac8f4
Revises: 6df03f4b1efb
Create Date: 2023-01-19 11:41:41.062228

"""
from alembic import op
import sqlalchemy as db
from dagster._core.storage.migration.utils import has_index, has_table
from sqlalchemy.dialects import sqlite
from dagster._core.storage.sql import get_current_timestamp

# revision identifiers, used by Alembic.
revision = 'e62c379ac8f4'
down_revision = '6df03f4b1efb'
branch_labels = None
depends_on = None


def upgrade():
    if not has_table("runtime_partitions"):
        op.create_table(
            "runtime_partitions",
            db.Column(
                "id",
                db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
                primary_key=True,
                autoincrement=True,
            ),
            db.Column("partitions_def_name", db.Text, nullable=False),
            db.Column("partition_key", db.Text, nullable=False),
            db.Column("create_timestamp", db.DateTime, server_default=get_current_timestamp()),
        )
        op.create_index(
            "idx_runtime_partitions", "runtime_partitions", ["partitions_def_name", "partition_key"]
        )


def downgrade():
    if has_index("runtime_partitions", "idx_runtime_partitions"):
        op.drop_index("idx_runtime_partitions")

    if has_table("runtime_partitions"):
        op.drop_table("runtime_partitions")
