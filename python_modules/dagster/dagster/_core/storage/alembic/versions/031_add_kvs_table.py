"""add kvs table.

Revision ID: 5e139331e376
Revises: 6860f830e40c
Create Date: 2022-06-06 15:48:51.559562

"""
import sqlalchemy as db
from alembic import op
from dagster._core.storage.migration.utils import has_index, has_table

# revision identifiers, used by Alembic.
revision = "5e139331e376"
down_revision = "6860f830e40c"
branch_labels = None
depends_on = None


def upgrade():
    if not has_table("kvs"):
        op.create_table(
            "kvs",
            db.Column("key", db.Text, nullable=False),
            db.Column("value", db.Text),
        )

    if not has_index("kvs", "idx_kvs_keys_unique"):
        op.create_index(
            "idx_kvs_keys_unique",
            "kvs",
            ["key"],
            unique=True,
            mysql_length={"key": 64},
        )


def downgrade():
    if has_index("kvs", "idx_kvs_keys_unique"):
        op.drop_index("idx_kvs_keys_unique")

    if has_table("kvs"):
        op.drop_table("kvs")
