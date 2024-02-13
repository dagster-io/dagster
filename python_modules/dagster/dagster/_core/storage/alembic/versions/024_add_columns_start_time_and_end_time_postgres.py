"""Add columns start_time and end_time.

Revision ID: 42add02bf976
Revises: f78059038d01
Create Date: 2021-12-20 13:41:14.924529

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "42add02bf976"
down_revision = "f78059038d01"
branch_labels = None
depends_on = None


def upgrade():
    inspector = inspect(op.get_bind())
    has_tables = inspector.get_table_names()

    if "runs" in has_tables:
        columns = [x.get("name") for x in inspector.get_columns("runs")]
        with op.batch_alter_table("runs") as batch_op:
            if "start_time" not in columns:
                batch_op.add_column(sa.Column("start_time", sa.Float))
            if "end_time" not in columns:
                batch_op.add_column(sa.Column("end_time", sa.Float))


def downgrade():
    inspector = inspect(op.get_bind())
    has_tables = inspector.get_table_names()
    if "runs" in has_tables:
        columns = [x.get("name") for x in inspector.get_columns("runs")]

        with op.batch_alter_table("runs") as batch_op:
            if "start_time" in columns:
                batch_op.drop_column("start_time")
            if "end_time" in columns:
                batch_op.drop_column("end_time")
