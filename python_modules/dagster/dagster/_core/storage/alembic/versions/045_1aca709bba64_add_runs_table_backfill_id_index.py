"""add runs table backfill_id index

Revision ID: 1aca709bba64
Revises: 63d7a8ec641a
Create Date: 2024-10-23 17:36:39.876876

"""

from alembic import op
from dagster._core.storage.migration.utils import has_index, has_table

# revision identifiers, used by Alembic.
revision = "1aca709bba64"
down_revision = "63d7a8ec641a"
branch_labels = None
depends_on = None


def upgrade():
    if not has_table("runs"):
        return

    if not has_index("runs", "idx_runs_by_backfill_id"):
        op.create_index(
            "idx_runs_by_backfill_id",
            "runs",
            ["backfill_id", "id"],
            unique=False,
            postgresql_concurrently=True,
            mysql_length={"backfill_id": 255},
        )


def downgrade():
    if not has_table("runs"):
        return

    if has_index("runs", "idx_runs_by_backfill_id"):
        op.drop_index(
            "idx_runs_by_backfill_id",
            "runs",
            postgresql_concurrently=True,
        )
