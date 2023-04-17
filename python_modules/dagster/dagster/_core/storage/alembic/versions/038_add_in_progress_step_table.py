"""add in progress step table

Revision ID: 5771160a95ad
Revises: d9092588866f
Create Date: 2023-04-10 19:26:23.232433

"""
import sqlalchemy as db
from alembic import op
from dagster._core.storage.migration.utils import has_table
from dagster._core.storage.sql import get_current_timestamp
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = "5771160a95ad"
down_revision = "d9092588866f"
branch_labels = None
depends_on = None


def upgrade():
    if not has_table("concurrency_slots"):
        op.create_table(
            "concurrency_slots",
            db.Column(
                "id",
                db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
                primary_key=True,
                autoincrement=True,
            ),
            db.Column("concurrency_key", db.Text, nullable=False),
            db.Column("run_id", db.Text),
            db.Column("step_key", db.Text),
            db.Column("create_timestamp", db.DateTime, server_default=get_current_timestamp()),
        )


def downgrade():
    if has_table("concurrency_slots"):
        op.drop_table("concurrency_slots")
