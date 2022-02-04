"""add_columns_start_time_and_end_time

Revision ID: f78059038d01
Revises: 29a8e9d74220
Create Date: 2022-01-25 09:26:35.820814

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import reflection

# revision identifiers, used by Alembic.
revision = "f78059038d01"
down_revision = "29a8e9d74220"
branch_labels = None
depends_on = None

# pylint: disable=no-member


def upgrade():
    bind = op.get_context().bind
    inspector = reflection.Inspector.from_engine(bind)
    has_tables = inspector.get_table_names()

    if "runs" in has_tables:
        columns = [x.get("name") for x in inspector.get_columns("runs")]
        with op.batch_alter_table("runs") as batch_op:
            if "start_time" not in columns:
                batch_op.add_column(sa.Column("start_time", sa.Float))
            if "end_time" not in columns:
                batch_op.add_column(sa.Column("end_time", sa.Float))


def downgrade():
    bind = op.get_context().bind
    inspector = reflection.Inspector.from_engine(bind)
    has_tables = inspector.get_table_names()
    if "runs" in has_tables:
        columns = [x.get("name") for x in inspector.get_columns("runs")]

        with op.batch_alter_table("runs") as batch_op:
            if "start_time" in columns:
                batch_op.drop_column("start_time")
            if "end_time" in columns:
                batch_op.drop_column("end_time")
