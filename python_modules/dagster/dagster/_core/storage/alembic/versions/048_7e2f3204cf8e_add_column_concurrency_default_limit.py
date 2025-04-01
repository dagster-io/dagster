"""add column concurrency default limit

Revision ID: 7e2f3204cf8e
Revises: 6b7fb194ff9c
Create Date: 2025-01-13 15:19:19.331752

"""

import sqlalchemy as sa
from alembic import op
from dagster._core.storage.migration.utils import has_column, has_table

# revision identifiers, used by Alembic.
revision = "7e2f3204cf8e"
down_revision = "6b7fb194ff9c"
branch_labels = None
depends_on = None


def upgrade():
    if has_table("concurrency_limits"):
        if not has_column("concurrency_limits", "using_default_limit"):
            op.add_column(
                "concurrency_limits",
                sa.Column(
                    "using_default_limit",
                    sa.Boolean(),
                    nullable=False,
                    default=False,
                    server_default=sa.false(),
                ),
            )


def downgrade():
    if has_table("concurrency_limits"):
        if has_column("concurrency_limits", "using_default_limit"):
            op.drop_column("concurrency_limits", "using_default_limit")
