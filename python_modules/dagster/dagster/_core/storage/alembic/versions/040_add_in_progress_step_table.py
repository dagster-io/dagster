"""add in progress step table

Revision ID: 5771160a95ad
Revises: d3a4c9e87af3
Create Date: 2023-04-10 19:26:23.232433

"""
import sqlalchemy as db
from alembic import op
from dagster._core.storage.migration.utils import has_index, has_table
from dagster._core.storage.sql import get_current_timestamp
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = "5771160a95ad"
down_revision = "d3a4c9e87af3"
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
            db.Column("deleted", db.Boolean, nullable=False, default=False),
            db.Column("create_timestamp", db.DateTime, server_default=get_current_timestamp()),
        )

    if not has_table("pending_steps"):
        op.create_table(
            "pending_steps",
            db.Column(
                "id",
                db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
                primary_key=True,
                autoincrement=True,
            ),
            db.Column("concurrency_key", db.Text, nullable=False),
            db.Column("run_id", db.Text),
            db.Column("step_key", db.Text),
            db.Column("priority", db.Integer),
            db.Column("assigned_timestamp", db.DateTime),
            db.Column("create_timestamp", db.DateTime, server_default=get_current_timestamp()),
        )
        op.create_index(
            "idx_pending_steps",
            "pending_steps",
            ["concurrency_key", "run_id", "step_key"],
            mysql_length={"concurrency_key": 255, "run_id": 255, "step_key": 32},
            unique=True,
        )


def downgrade():
    if has_table("concurrency_slots"):
        op.drop_table("concurrency_slots")

    if has_table("pending_steps"):
        if has_index("pending_steps", "idx_pending_steps"):
            op.drop_index("idx_pending_steps", "pending_steps")
        op.drop_table("pending_steps")
