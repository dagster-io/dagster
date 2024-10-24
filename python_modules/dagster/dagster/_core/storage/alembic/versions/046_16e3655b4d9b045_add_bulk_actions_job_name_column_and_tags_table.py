"""add bulk_actions job_name column and backfill_tags table

Revision ID: 16e3655b4d9b
Revises: 1aca709bba64
Create Date: 2024-10-23 13:13:13.390846

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = "16e3655b4d9b"
down_revision = "1aca709bba64"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    has_tables = inspector.get_table_names()

    if "bulk_actions" in has_tables:
        columns = [x.get("name") for x in inspector.get_columns("bulk_actions")]
        if "job_name" not in columns:
            op.add_column("bulk_actions", sa.Column("job_name", sa.Text(), nullable=True))

    if "backfill_tags" not in has_tables:
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
            sa.Column("bulk_actions_storage_id", sa.BigInteger(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade():
    inspector = sa.inspect(op.get_bind())
    has_tables = inspector.get_table_names()
    if "bulk_actions" in has_tables:
        columns = [x.get("name") for x in inspector.get_columns("bulk_actions")]
        if "job_name" in columns:
            op.drop_column("bulk_actions", "job_name")

    if "backfill_tags" in has_tables:
        op.drop_table("backfill_tags")
