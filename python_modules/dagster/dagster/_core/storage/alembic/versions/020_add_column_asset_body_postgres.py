"""add column asset body.

Revision ID: 7cba9eeaaf1d
Revises: f0367d611631
Create Date: 2021-03-17 16:40:52.449012

"""

from dagster._core.storage.migration.utils import add_asset_details_column

# revision identifiers, used by Alembic.
revision = "7cba9eeaaf1d"
down_revision = "f0367d611631"
branch_labels = None
depends_on = None


def upgrade():
    add_asset_details_column()


def downgrade():
    pass
