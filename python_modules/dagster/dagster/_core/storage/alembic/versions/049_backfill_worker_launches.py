"""Add the durable backfill worker launch ledger.

Revision ID: 4e7a9c31b602
Revises: 29b539ebc72a
"""

import sqlalchemy as sa
from alembic import op
from dagster._core.storage.migration.utils import has_column, has_index, has_table
from dagster._core.storage.runs.schema import BackfillWorkerLaunchesTable

revision = "4e7a9c31b602"
down_revision = "29b539ebc72a"
branch_labels = None
depends_on = None


def upgrade():
    if has_table("runs"):
        if not has_column("runs", "auto_retry_intent"):
            op.add_column("runs", sa.Column("auto_retry_intent", sa.String(255), nullable=True))
        if not has_index("runs", "idx_runs_auto_retry_intent"):
            op.create_index(
                "idx_runs_auto_retry_intent", "runs", ["auto_retry_intent"], unique=True
            )
        if not has_table(BackfillWorkerLaunchesTable.name):
            BackfillWorkerLaunchesTable.create(op.get_bind())


def downgrade():
    if has_table(BackfillWorkerLaunchesTable.name):
        BackfillWorkerLaunchesTable.drop(op.get_bind())
    if has_table("runs"):
        if has_index("runs", "idx_runs_auto_retry_intent"):
            op.drop_index("idx_runs_auto_retry_intent", "runs")
        if has_column("runs", "auto_retry_intent"):
            op.drop_column("runs", "auto_retry_intent")
