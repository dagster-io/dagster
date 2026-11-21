"""add create_timestamp index to asset_daemon_asset_evaluations

Revision ID: 2c319113493c
Revises: 29b539ebc72a
Create Date: 2026-10-21 14:40:12.318402

"""

from alembic import op
from dagster._core.storage.migration.utils import has_index, has_table

# revision identifiers, used by Alembic.
revision = "2c319113493c"
down_revision = "29b539ebc72a"
branch_labels = None
depends_on = None


def upgrade():
    if not has_table("asset_daemon_asset_evaluations"):
        return

    if not has_index(
        "asset_daemon_asset_evaluations", "idx_asset_daemon_asset_evaluations_create_timestamp"
    ):
        op.create_index(
            "idx_asset_daemon_asset_evaluations_create_timestamp",
            "asset_daemon_asset_evaluations",
            ["create_timestamp"],
            unique=False,
            postgresql_concurrently=True,
        )


def downgrade():
    if not has_table("asset_daemon_asset_evaluations"):
        return

    if has_index(
        "asset_daemon_asset_evaluations", "idx_asset_daemon_asset_evaluations_create_timestamp"
    ):
        op.drop_index(
            "idx_asset_daemon_asset_evaluations_create_timestamp",
            "asset_daemon_asset_evaluations",
            postgresql_concurrently=True,
        )
