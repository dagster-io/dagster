"""add column "mode".

Revision ID: 7f2b1a4ca7a5
Revises: ddcc6d7244c6
Create Date: 2021-07-06 13:49:53.668345

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "7f2b1a4ca7a5"
down_revision = "ddcc6d7244c6"
branch_labels = None
depends_on = None


def upgrade():
    inspector = inspect(op.get_bind())
    has_tables = inspector.get_table_names()

    if "runs" in has_tables:
        columns = [x.get("name") for x in inspector.get_columns("runs")]
        with op.batch_alter_table("runs") as batch_op:
            if "mode" not in columns:
                batch_op.add_column(sa.Column("mode", sa.Text))


def downgrade():
    inspector = inspect(op.get_bind())
    has_tables = inspector.get_table_names()
    if "runs" in has_tables:
        columns = [x.get("name") for x in inspector.get_columns("runs")]

        with op.batch_alter_table("runs") as batch_op:
            if "mode" in columns:
                batch_op.drop_column("mode")
