"""extract asset_keys index columns

Revision ID: 7b8304b4429d
Revises: 1a2d72f6b24e
Create Date: 2021-07-06 10:52:50.862728

"""
from dagster.core.storage.migration.utils import extract_asset_keys_idx_columns

# revision identifiers, used by Alembic.
revision = "7b8304b4429d"
down_revision = "1a2d72f6b24e"
branch_labels = None
depends_on = None


def upgrade():
    extract_asset_keys_idx_columns()


def downgrade():
    pass
