"""Add asset daemon asset evaluations table

Revision ID: d3a4c9e87af3
Revises: 701913684cb4
Create Date: 2023-05-09 11:50:38.931820

"""

import sqlalchemy as db
from alembic import op
from dagster._core.storage.migration.utils import has_index, has_table
from dagster._core.storage.sql import get_sql_current_timestamp
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = "d3a4c9e87af3"
down_revision = "701913684cb4"
branch_labels = None
depends_on = None


def upgrade():
    if not has_table("asset_daemon_asset_evaluations"):
        op.create_table(
            "asset_daemon_asset_evaluations",
            db.Column(
                "id",
                db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
                primary_key=True,
                autoincrement=True,
            ),
            db.Column(
                "evaluation_id",
                db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
                index=True,
            ),
            db.Column("asset_key", db.Text),
            db.Column("asset_evaluation_body", db.Text),
            db.Column("num_requested", db.Integer),
            db.Column("num_skipped", db.Integer),
            db.Column("num_discarded", db.Integer),
            db.Column("create_timestamp", db.DateTime, server_default=get_sql_current_timestamp()),
        )
        op.create_index(
            "idx_asset_daemon_asset_evaluations_asset_key_evaluation_id",
            "asset_daemon_asset_evaluations",
            ["asset_key", "evaluation_id"],
            mysql_length={"asset_key": 64},
            unique=True,
        )


def downgrade():
    if has_index(
        "asset_daemon_asset_evaluations",
        "idx_asset_daemon_asset_evaluations_asset_key_evaluation_id",
    ):
        op.drop_index(
            "idx_asset_daemon_asset_evaluations_asset_key_evaluation_id",
            "asset_daemon_asset_evaluations",
        )
    if has_table("asset_daemon_asset_evaluations"):
        op.drop_table("asset_daemon_asset_evaluations")
