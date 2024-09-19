"""add tick selector index.

Revision ID: d32d1d6de793
Revises: c892b3fe0a9f
Create Date: 2022-03-25 10:29:10.895341

"""

from dagster._core.storage.migration.utils import create_tick_selector_index

# revision identifiers, used by Alembic.
revision = "d32d1d6de793"
down_revision = "c892b3fe0a9f"
branch_labels = None
depends_on = None


def upgrade():
    create_tick_selector_index()


def downgrade():
    pass
