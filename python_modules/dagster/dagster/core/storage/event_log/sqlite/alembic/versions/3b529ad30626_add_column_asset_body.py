"""add column asset body

Revision ID: 3b529ad30626
Revises: 72686963a802
Create Date: 2021-03-17 16:38:09.418235

"""
from dagster.core.storage.migration.utils import add_asset_details_column

# revision identifiers, used by Alembic.
revision = "3b529ad30626"
down_revision = "72686963a802"
branch_labels = None
depends_on = None


def upgrade():
    add_asset_details_column()


def downgrade():
    pass
