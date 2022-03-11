"""add run partition columns

Revision ID: 375e95bad550
Revises: 224640159acf
Create Date: 2021-01-05 14:39:50.395455

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import reflection

# pylint: disable=no-member

# revision identifiers, used by Alembic.
revision = "375e95bad550"
down_revision = "224640159acf"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_context().bind
    inspector = reflection.Inspector.from_engine(bind)
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
    bind = op.get_context().bind
    inspector = reflection.Inspector.from_engine(bind)
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
