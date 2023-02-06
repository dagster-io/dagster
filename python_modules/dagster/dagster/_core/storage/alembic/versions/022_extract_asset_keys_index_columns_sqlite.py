"""extract asset_keys index columns.

Revision ID: e784752027a6
Revises: 7b8304b4429d
Create Date: 2021-07-06 10:51:26.269010

"""
from dagster._core.storage.migration.utils import extract_asset_keys_idx_columns

# revision identifiers, used by Alembic.
revision = "e784752027a6"
down_revision = "7b8304b4429d"
branch_labels = None
depends_on = None


def upgrade():
    extract_asset_keys_idx_columns()


def downgrade():
    pass
