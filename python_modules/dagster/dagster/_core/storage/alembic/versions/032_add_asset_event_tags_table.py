"""add asset event tags table

Revision ID: b205615425e4
Revises: 5e139331e376
Create Date: 2022-10-12 15:43:46.007624

"""
from alembic import op
import sqlalchemy as db

from dagster._core.storage.migration.utils import has_index, has_table

# revision identifiers, used by Alembic.
revision = 'b205615425e4'
down_revision = '5e139331e376'
branch_labels = None
depends_on = None


def upgrade():
    if not has_table("asset_event_tags"):
        op.create_table(
            "asset_event_tags",
            db.Column("id", db.Integer, primary_key=True, autoincrement=True),
            db.Column("event_id", db.Integer, db.ForeignKey("event_logs.id", ondelete="CASCADE")),
            db.Column("key", db.Text),
            db.Column("value", db.Text),
        )

    if not has_index("asset_event_tags", "idx_asset_event_tags"):
        op.create_index(
            "idx_asset_event_tags",
            "asset_event_tags",
            ["key", "value"],
            unique=False,
            mysql_length={"key": 64, "value": 64},
        )


def downgrade():
    if has_index("asset_event_tags", "idx_asset_event_tags"):
        op.drop_index("idx_asset_event_tags")

    if has_table("asset_event_tags"):
        op.drop_table("asset_event_tags")
