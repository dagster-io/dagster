"""add tick selector index

Revision ID: 721d858e1dda
Revises: b601eb913efa
Create Date: 2022-03-25 10:28:29.065161

"""
from dagster.core.storage.migration.utils import create_tick_selector_index

# revision identifiers, used by Alembic.
revision = "721d858e1dda"
down_revision = "b601eb913efa"
branch_labels = None
depends_on = None


def upgrade():
    create_tick_selector_index()


def downgrade():
    pass
