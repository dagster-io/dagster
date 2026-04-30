"""add display_label column to dynamic_partitions table

Revision ID: a16d5b32c4e1
Revises: 29b539ebc72a
Create Date: 2026-04-07 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from dagster._core.storage.migration.utils import has_column, has_table

# revision identifiers, used by Alembic.
revision = "a16d5b32c4e1"
down_revision = "29b539ebc72a"
branch_labels = None
depends_on = None


def upgrade():
    if has_table("dynamic_partitions"):
        if not has_column("dynamic_partitions", "display_label"):
            op.add_column(
                "dynamic_partitions",
                sa.Column("display_label", sa.Text(), nullable=True),
            )


def downgrade():
    if has_table("dynamic_partitions"):
        if has_column("dynamic_partitions", "display_label"):
            op.drop_column("dynamic_partitions", "display_label")
