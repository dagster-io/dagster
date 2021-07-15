"""add column mode

Revision ID: ddcc6d7244c6
Revises: 7cba9eeaaf1d
Create Date: 2021-07-06 13:56:08.987201

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import reflection

# revision identifiers, used by Alembic.
revision = "ddcc6d7244c6"
down_revision = "7cba9eeaaf1d"
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
            if "mode" not in columns:
                batch_op.add_column(sa.Column("mode", sa.Text))


def downgrade():
    bind = op.get_context().bind
    inspector = reflection.Inspector.from_engine(bind)
    has_tables = inspector.get_table_names()
    if "runs" in has_tables:
        columns = [x.get("name") for x in inspector.get_columns("runs")]

        with op.batch_alter_table("runs") as batch_op:
            if "mode" in columns:
                batch_op.drop_column("mode")
