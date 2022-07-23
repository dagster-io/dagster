"""add tick selector index

Revision ID: b601eb913efa
Revises: d32d1d6de793
Create Date: 2022-03-25 10:28:53.372766

"""
from dagster.core.storage.migration.utils import create_tick_selector_index

# revision identifiers, used by Alembic.
revision = "b601eb913efa"
down_revision = "d32d1d6de793"
branch_labels = None
depends_on = None


def upgrade():
    create_tick_selector_index()


def downgrade():
    pass
