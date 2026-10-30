"""add create_timestamp index to asset_daemon_asset_evaluations

Revision ID: 6b673045fd0e
Revises: 29b539ebc72a
Create Date: 2026-10-24 21:37:47

"""

from alembic import op
from dagster._core.storage.migration.utils import has_index, has_table

# revision identifiers, used by Alembic.
revision = "6b673045fd0e"
down_revision = "29b539ebc72a"
branch_labels = None
depends_on = None


def upgrade():
    if has_table("asset_daemon_asset_evaluations"):
        if not has_index(
            "asset_daemon_asset_evaluations",
            "idx_asset_daemon_asset_evaluations_create_timestamp",
        ):
            op.create_index(
                "idx_asset_daemon_asset_evaluations_create_timestamp",
                "asset_daemon_asset_evaluations",
                ["create_timestamp"],
                unique=False,
                postgresql_concurrently=True,
            )


def downgrade():
    if has_table("asset_daemon_asset_evaluations"):
        if has_index(
            "asset_daemon_asset_evaluations",
            "idx_asset_daemon_asset_evaluations_create_timestamp",
        ):
            op.drop_index(
                "idx_asset_daemon_asset_evaluations_create_timestamp",
                "asset_daemon_asset_evaluations",
                postgresql_concurrently=True,
            )
