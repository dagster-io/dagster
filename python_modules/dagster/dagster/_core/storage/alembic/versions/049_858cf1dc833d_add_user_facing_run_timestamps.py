"""add user facing run timestamps

Revision ID: 858cf1dc833d
Revises: 7e2f3204cf8e
Create Date: 2025-04-17 13:25:02.653808

"""

import sqlalchemy as sa
from alembic import op
from dagster._core.storage.migration.utils import has_column, has_table

# revision identifiers, used by Alembic.
revision = "858cf1dc833d"
down_revision = "7e2f3204cf8e"
branch_labels = None
depends_on = None


def upgrade():
    if has_table("runs"):
        op.add_column("runs", sa.Column("run_creation_time", sa.Float))
        op.add_column("runs", sa.Column("public_update_timestamp", sa.Float))


def downgrade():
    if has_table("runs"):
        if has_column("runs", "run_creation_time"):
            op.drop_column("runs", "run_creation_time")
        if has_column("runs", "public_update_timestamp"):
            op.drop_column("runs", "public_update_timestamp")
