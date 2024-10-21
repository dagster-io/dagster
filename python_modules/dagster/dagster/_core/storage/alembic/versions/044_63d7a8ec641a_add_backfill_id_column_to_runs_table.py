"""add backfill_id column to runs table

Revision ID: 63d7a8ec641a
Revises: 284a732df317
Create Date: 2024-10-18 15:56:30.002452

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "63d7a8ec641a"
down_revision = "284a732df317"
branch_labels = None
depends_on = None


def upgrade():
    inspector = inspect(op.get_bind())
    has_tables = inspector.get_table_names()

    if "runs" in has_tables:
        columns = [x.get("name") for x in inspector.get_columns("runs")]
        with op.batch_alter_table("runs") as batch_op:
            if "backfill_id" not in columns:
                batch_op.add_column(sa.Column("backfill_id", sa.String(255), nullable=True))


def downgrade():
    inspector = inspect(op.get_bind())
    has_tables = inspector.get_table_names()
    if "runs" in has_tables:
        columns = [x.get("name") for x in inspector.get_columns("runs")]

        with op.batch_alter_table("runs") as batch_op:
            if "backfill_id" in columns:
                batch_op.drop_column("backfill_id")
