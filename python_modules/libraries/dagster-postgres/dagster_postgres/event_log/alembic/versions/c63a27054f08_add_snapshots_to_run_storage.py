"""add snapshots to run storage

Revision ID: c63a27054f08
Revises: 1ebdd7a9686f
Create Date: 2020-04-09 05:57:20.639458

"""
import sqlalchemy as sa
from alembic import op
from dagster.core.storage.migration.utils import has_column, has_table

# alembic magic breaks pylint
# pylint: disable=no-member

# revision identifiers, used by Alembic.
revision = "c63a27054f08"
down_revision = "1ebdd7a9686f"
branch_labels = None
depends_on = None


def upgrade():
    if not has_table("runs"):
        return

    if not has_table("snapshots"):
        op.create_table(
            "snapshots",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True, nullable=False),
            sa.Column("snapshot_id", sa.String(255), unique=True, nullable=False),
            sa.Column("snapshot_body", sa.LargeBinary, nullable=False),
            sa.Column("snapshot_type", sa.String(63), nullable=False),
        )

    if not has_column("runs", "snapshot_id"):
        op.add_column(
            "runs",
            sa.Column("snapshot_id", sa.String(255), sa.ForeignKey("snapshots.snapshot_id")),
        )


def downgrade():
    if has_table("snapshots"):
        op.drop_table("snapshots")

    if not has_table("runs"):
        return

    if has_column("runs", "snapshot_id"):
        op.drop_column("runs", "snapshot_id")
