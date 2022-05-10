"""add columns start_time and end_time

Revision ID: f4eed4c26e2c
Revises: 42add02bf976
Create Date: 2021-12-20 13:18:31.122983

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import reflection

# revision identifiers, used by Alembic.
revision = "f4eed4c26e2c"
down_revision = "42add02bf976"
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
