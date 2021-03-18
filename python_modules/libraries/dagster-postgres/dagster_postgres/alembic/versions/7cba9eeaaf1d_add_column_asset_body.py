"""add column asset body

Revision ID: 7cba9eeaaf1d
Revises: 3778078a3582
Create Date: 2021-03-17 16:40:52.449012

"""
from dagster.core.storage.migration.utils import add_asset_details_column

# revision identifiers, used by Alembic.
revision = "7cba9eeaaf1d"
down_revision = "3778078a3582"
branch_labels = None
depends_on = None


def upgrade():
    add_asset_details_column()


def downgrade():
    pass
