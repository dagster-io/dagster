"""add snapshots to run storage

Revision ID: c63a27054f08
Revises: 3b1e175a2be3
Create Date: 2020-04-09 05:57:20.639458

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

from dagster._core.storage.migration.utils import has_column, has_table

# alembic magic breaks pylint
# pylint: disable=no-member

# revision identifiers, used by Alembic.
revision = "c63a27054f08"
down_revision = "3b1e175a2be3"
branch_labels = None
depends_on = None


def upgrade():
    inspector = inspect(op.get_bind())

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
        if "sqlite" in inspector.dialect.dialect_description:
            # Sqlite does not support adding foreign keys to existing
            # tables, so we are forced to fallback on this witchcraft.
            # See https://alembic.sqlalchemy.org/en/latest/batch.html#dealing-with-referencing-foreign-keys
            # for additional context
            with op.batch_alter_table("runs") as batch_op:
                batch_op.execute("PRAGMA foreign_keys = OFF;")
                batch_op.add_column(
                    sa.Column(
                        "snapshot_id",
                        sa.String(255),
                        sa.ForeignKey(
                            "snapshots.snapshot_id",
                            name="fk_runs_snapshot_id_snapshots_snapshot_id",
                        ),
                    ),
                )
            op.execute("PRAGMA foreign_keys = ON;")
        else:
            op.add_column(
                "runs",
                sa.Column("snapshot_id", sa.String(255), sa.ForeignKey("snapshots.snapshot_id")),
            )


def downgrade():
    inspector = inspect(op.get_bind())

    if not has_table("runs"):
        return

    if has_column("runs", "snapshot_id"):
        if "sqlite" in inspector.dialect.dialect_description:
            with op.batch_alter_table("runs") as batch_op:
                batch_op.drop_column("snapshot_id")
        else:
            op.drop_column("runs", "snapshot_id")

    if has_table("snapshots"):
        op.drop_table("snapshots")
