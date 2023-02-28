"""add primary key cols

Revision ID: d9092588866f
Revises: e62c379ac8f4
Create Date: 2023-03-03 14:20:07.082211

"""
import sqlalchemy as db
from alembic import op
from dagster._core.storage.migration.utils import has_column, has_primary_key, has_table
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = "d9092588866f"
down_revision = "e62c379ac8f4"
branch_labels = None
depends_on = None


def upgrade():
    has_primary_key("runs")
    if has_table("kvs") and not has_column("kvs", "id"):
        op.add_column(
            "kvs",
            db.Column(
                "id",
                db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
                unique=True,
                primary_key=has_primary_key("kvs"),
                autoincrement=True,
            ),
        )

    if has_table("instance_info") and not has_column("instance_info", "id"):
        op.add_column(
            "instance_info",
            db.Column(
                "id",
                db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
                unique=True,
                primary_key=has_primary_key("kvs"),
                autoincrement=True,
            ),
        )

    if has_table("daemon_heartbeats") and not has_column("daemon_heartbeats", "id"):
        op.add_column(
            "daemon_heartbeats",
            db.Column(
                "id",
                db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
                unique=True,
                primary_key=has_primary_key("kvs"),
                autoincrement=True,
            ),
        )


def downgrade():
    if has_table("kvs") and has_column("kvs", "id"):
        op.drop_column("kvs", "id")

    if has_table("instance_info") and has_column("instance_info", "id"):
        op.drop_column("instance_info", "id")

    if has_table("daemon_heartbeats") and has_column("daemon_heartbeats", "id"):
        op.drop_column("daemon_heartbeats", "id")
