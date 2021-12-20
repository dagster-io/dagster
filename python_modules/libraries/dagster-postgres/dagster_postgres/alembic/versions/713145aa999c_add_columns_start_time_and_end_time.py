"""add columns start_time and end_time

Revision ID: 713145aa999c
Revises: f4b6a4885876
Create Date: 2021-12-20 13:32:49.322107

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import reflection

# revision identifiers, used by Alembic.
revision = "713145aa999c"
down_revision = "f4b6a4885876"
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
