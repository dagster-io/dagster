"""add column asset body

Revision ID: f0367d611631
Revises: 72686963a802
Create Date: 2021-03-17 16:41:14.457324

"""
from dagster.core.storage.migration.utils import add_asset_details_column

# revision identifiers, used by Alembic.
revision = "f0367d611631"
down_revision = "72686963a802"
branch_labels = None
depends_on = None


def upgrade():
    add_asset_details_column()


def downgrade():
    pass
