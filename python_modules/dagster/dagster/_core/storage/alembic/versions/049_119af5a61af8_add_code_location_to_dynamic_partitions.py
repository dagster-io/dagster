"""add code_location_name to dynamic_partitions table

Revision ID: 119af5a61af8
Revises: 29b539ebc72a
Create Date: 2026-04-30

"""

import sqlalchemy as sa
from alembic import op
from dagster._core.storage.migration.utils import has_column, has_index, has_table

revision = "119af5a61af8"
down_revision = "29b539ebc72a"
branch_labels = None
depends_on = None


def upgrade():
    if not has_table("dynamic_partitions"):
        return

    if not has_column("dynamic_partitions", "code_location_name"):
        op.add_column(
            "dynamic_partitions",
            sa.Column("code_location_name", sa.Text(), nullable=True),
        )

    # Replace the unique index (which cannot scope NULLs correctly) with a
    # non-unique composite index. App-level dedup in add_dynamic_partitions
    # ensures idempotency without relying on a DB-level unique constraint.
    if has_index("dynamic_partitions", "idx_dynamic_partitions"):
        op.drop_index("idx_dynamic_partitions", table_name="dynamic_partitions")

    op.create_index(
        "idx_dynamic_partitions",
        "dynamic_partitions",
        ["code_location_name", "partitions_def_name", "partition"],
        mysql_length={"code_location_name": 64, "partitions_def_name": 64, "partition": 64},
    )


def downgrade():
    if not has_table("dynamic_partitions"):
        return

    if has_index("dynamic_partitions", "idx_dynamic_partitions"):
        op.drop_index("idx_dynamic_partitions", table_name="dynamic_partitions")

    # Scoped rows (code_location_name IS NOT NULL) cannot survive the column drop.
    # Unscoped rows may have duplicates if concurrent inserts raced after the unique
    # index was removed in upgrade(). Delete both to ensure the UNIQUE index below
    # can be recreated without a constraint violation.
    op.execute("DELETE FROM dynamic_partitions WHERE code_location_name IS NOT NULL")
    op.execute(
        "DELETE FROM dynamic_partitions WHERE id NOT IN ("
        "  SELECT MIN(id) FROM dynamic_partitions"
        "  GROUP BY partitions_def_name, partition"
        ")"
    )

    op.create_index(
        "idx_dynamic_partitions",
        "dynamic_partitions",
        ["partitions_def_name", "partition"],
        mysql_length={"partitions_def_name": 64, "partition": 64},
        unique=True,
    )

    if has_column("dynamic_partitions", "code_location_name"):
        op.drop_column("dynamic_partitions", "code_location_name")
