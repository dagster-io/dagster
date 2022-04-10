"""add tick selector index

Revision ID: b601eb913efa
Revises: 16e3115a602a
Create Date: 2022-03-25 10:28:53.372766

"""
from dagster.core.storage.migration.utils import create_tick_selector_index

# revision identifiers, used by Alembic.
revision = "b601eb913efa"
down_revision = "16e3115a602a"
branch_labels = None
depends_on = None


def upgrade():
    create_tick_selector_index()


def downgrade():
    pass
