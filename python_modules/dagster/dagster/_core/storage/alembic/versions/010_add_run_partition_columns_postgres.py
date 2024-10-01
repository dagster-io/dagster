"""add run partition columns.

Revision ID: f3e43ff66603
Revises: 9483999bad92
Create Date: 2021-01-05 15:21:52.820686

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "f3e43ff66603"
down_revision = "9483999bad92"
branch_labels = None
depends_on = None


def upgrade():
    inspector = inspect(op.get_bind())
    has_tables = inspector.get_table_names()
    if "runs" in has_tables:
        columns = [x.get("name") for x in inspector.get_columns("runs")]
        indices = [x.get("name") for x in inspector.get_indexes("runs")]
        with op.batch_alter_table("runs") as batch_op:
            if "partition" not in columns:
                batch_op.add_column(sa.Column("partition", sa.String))
            if "partition_set" not in columns:
                batch_op.add_column(sa.Column("partition_set", sa.String))
            if "idx_run_partitions" not in indices:
                batch_op.create_index(
                    "idx_run_partitions", ["partition_set", "partition"], unique=False
                )


def downgrade():
    inspector = inspect(op.get_bind())
    has_tables = inspector.get_table_names()
    if "runs" in has_tables:
        columns = [x.get("name") for x in inspector.get_columns("runs")]
        indices = [x.get("name") for x in inspector.get_indexes("runs")]

        with op.batch_alter_table("runs") as batch_op:
            if "partition" in columns:
                batch_op.drop_column("partition")
            if "partition_set" in columns:
                batch_op.drop_column("partition_set")
            if "idx_run_partitions" in indices:
                batch_op.drop_index("idx_run_partitions")
