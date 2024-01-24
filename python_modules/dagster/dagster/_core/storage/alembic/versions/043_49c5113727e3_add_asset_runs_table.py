"""add asset runs table

Revision ID: 49c5113727e3
Revises: 46b412388816
Create Date: 2024-01-24 11:37:28.995724

"""
import sqlalchemy as db
from alembic import op
from dagster._core.storage.migration.utils import has_table
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '49c5113727e3'
down_revision = '46b412388816'
branch_labels = None
depends_on = None


def upgrade():
    if not has_table("asset_runs"):
        op.create_table(
            "asset_runs",
            db.Column(
                "event_id",
                db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
                primary_key=True,
            ),
            db.Column("asset_key", db.Text, nullable=False),
            db.Column("run_id", db.String(255), nullable=False),
            db.Column("run_start_time", db.Float),
            db.Column("run_end_time", db.Float),
        )


def downgrade():
    if has_table("asset_runs"):
        op.drop_table("asset_runs")
