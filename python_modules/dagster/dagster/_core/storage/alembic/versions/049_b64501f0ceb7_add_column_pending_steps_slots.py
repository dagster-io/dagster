"""add column pending steps slots

Revision ID: b64501f0ceb7
Revises: 29b539ebc72a
Create Date: 2026-08-10 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from dagster._core.storage.migration.utils import has_column, has_table

# revision identifiers, used by Alembic.
revision = "b64501f0ceb7"
down_revision = "29b539ebc72a"
branch_labels = None
depends_on = None


def upgrade():
    if has_table("pending_steps"):
        if not has_column("pending_steps", "slots"):
            op.add_column("pending_steps", sa.Column("slots", sa.Integer(), nullable=True))


def downgrade():
    if has_table("pending_steps"):
        if has_column("pending_steps", "slots"):
            op.drop_column("pending_steps", "slots")
