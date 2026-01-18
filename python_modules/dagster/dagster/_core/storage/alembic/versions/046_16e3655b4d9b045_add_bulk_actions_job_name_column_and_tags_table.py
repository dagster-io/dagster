"""add bulk_actions job_name column and backfill_tags table

Revision ID: 16e3655b4d9b
Revises: 1aca709bba64
Create Date: 2024-10-23 13:13:13.390846

"""

import sqlalchemy as sa
from alembic import op
from dagster._core.storage.migration.utils import has_column, has_index, has_table
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = "16e3655b4d9b"
down_revision = "1aca709bba64"
branch_labels = None
depends_on = None


def upgrade():
    if has_table("bulk_actions"):
        if not has_column("bulk_actions", "job_name"):
            op.add_column("bulk_actions", sa.Column("job_name", sa.Text(), nullable=True))

    if not has_table("backfill_tags"):
        op.create_table(
            "backfill_tags",
            sa.Column(
                "id",
                sa.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
                primary_key=True,
                autoincrement=True,
            ),
            sa.Column("backfill_id", sa.String(length=255), nullable=True),
            sa.Column("key", sa.Text(), nullable=True),
            sa.Column("value", sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "idx_backfill_tags_backfill_id",
            "backfill_tags",
            ["backfill_id", "id"],
            unique=False,
            postgresql_concurrently=True,
        )


def downgrade():
    if has_table("bulk_actions"):
        if has_column("bulk_actions", "job_name"):
            op.drop_column("bulk_actions", "job_name")

    if has_table("backfill_tags"):
        if has_index("backfill_tags", "idx_backfill_tags_backfill_id"):
            op.drop_index(
                "idx_backfill_tags_backfill_id",
                "backfill_tags",
                postgresql_concurrently=True,
            )
        op.drop_table("backfill_tags")
