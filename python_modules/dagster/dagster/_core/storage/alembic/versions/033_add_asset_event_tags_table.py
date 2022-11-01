"""add_asset_event_tags_table

Revision ID: 958a9495162d
Revises: a00dd8d936a1
Create Date: 2022-10-25 10:00:50.954192

"""
import sqlalchemy as db
from alembic import op
from sqlalchemy.dialects import sqlite

from dagster._core.storage.migration.utils import has_index, has_table

# revision identifiers, used by Alembic.
revision = "958a9495162d"
down_revision = "a00dd8d936a1"
branch_labels = None
depends_on = None


def upgrade():
    if not has_table("asset_event_tags"):
        op.create_table(
            "asset_event_tags",
            db.Column(
                "id",
                db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
                primary_key=True,
                autoincrement=True,
            ),
            db.Column("event_id", db.Integer, db.ForeignKey("event_logs.id", ondelete="CASCADE")),
            db.Column("asset_key", db.Text, nullable=False),
            db.Column("key", db.Text, nullable=False),
            db.Column("value", db.Text),
            db.Column("event_timestamp", db.types.TIMESTAMP),
        )

    if not has_index("asset_event_tags", "idx_asset_event_tags"):
        op.create_index(
            "idx_asset_event_tags",
            "asset_event_tags",
            ["asset_key", "key", "value"],
            unique=False,
            mysql_length={"key": 64, "value": 64, "asset_key": 64},
        )

    if not has_index("asset_event_tags", "idx_asset_event_tags_event_id"):
        op.create_index(
            "idx_asset_event_tags_event_id",
            "asset_event_tags",
            ["event_id"],
            unique=False,
        )


def downgrade():
    if has_index("asset_event_tags", "idx_asset_event_tags"):
        op.drop_index("idx_asset_event_tags")

    if has_index("asset_event_tags", "idx_asset_event_tags_event_id"):
        op.drop_index("idx_asset_event_tags_event_id")

    if has_table("asset_event_tags"):
        op.drop_table("asset_event_tags")
