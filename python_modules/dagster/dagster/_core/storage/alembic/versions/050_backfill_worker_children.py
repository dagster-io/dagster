"""Allow physical child receipts in the backfill worker ledger.

Revision ID: 7f812ac46e90
Revises: 4e7a9c31b602
"""

import sqlalchemy as sa
from alembic import op
from dagster._core.storage.migration.utils import has_table

revision = "7f812ac46e90"
down_revision = "4e7a9c31b602"
branch_labels = None
depends_on = None


def upgrade():
    if has_table("backfill_worker_launches"):
        with op.batch_alter_table("backfill_worker_launches") as batch:
            batch.drop_constraint("ck_backfill_worker_launch_kind", type_="check")
            batch.alter_column("kind", existing_type=sa.String(4), type_=sa.String(16))
            batch.create_check_constraint(
                "ck_backfill_worker_launch_kind", "kind IN ('RUN', 'STEP', 'CHILD')"
            )


def downgrade():
    if has_table("backfill_worker_launches"):
        with op.batch_alter_table("backfill_worker_launches") as batch:
            batch.drop_constraint("ck_backfill_worker_launch_kind", type_="check")
            batch.alter_column("kind", existing_type=sa.String(16), type_=sa.String(4))
            batch.create_check_constraint(
                "ck_backfill_worker_launch_kind", "kind IN ('RUN', 'STEP')"
            )
