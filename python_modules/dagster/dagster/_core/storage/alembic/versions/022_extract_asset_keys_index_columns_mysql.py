"""extract asset_keys index columns.

Revision ID: 1a2d72f6b24e
Revises: 7f2b1a4ca7a5
Create Date: 2021-07-06 10:53:45.164780

"""
from dagster._core.storage.migration.utils import extract_asset_keys_idx_columns

# revision identifiers, used by Alembic.
revision = "1a2d72f6b24e"
down_revision = "7f2b1a4ca7a5"
branch_labels = None
depends_on = None


def upgrade():
    extract_asset_keys_idx_columns()


def downgrade():
    pass
