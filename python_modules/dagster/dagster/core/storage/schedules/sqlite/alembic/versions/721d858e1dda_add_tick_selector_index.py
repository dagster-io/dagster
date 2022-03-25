"""add tick selector index

Revision ID: 721d858e1dda
Revises: c892b3fe0a9f
Create Date: 2022-03-25 10:28:29.065161

"""
from dagster.core.storage.migration.utils import create_tick_selector_index

# revision identifiers, used by Alembic.
revision = "721d858e1dda"
down_revision = "c892b3fe0a9f"
branch_labels = None
depends_on = None


def upgrade():
    create_tick_selector_index()


def downgrade():
    pass
