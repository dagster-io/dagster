"""add column "mode"

Revision ID: 45fa602c43dc
Revises: 3b529ad30626
Create Date: 2021-07-06 14:04:04.808944

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "45fa602c43dc"
down_revision = "3b529ad30626"
branch_labels = None
depends_on = None

# pylint: disable=no-member


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
