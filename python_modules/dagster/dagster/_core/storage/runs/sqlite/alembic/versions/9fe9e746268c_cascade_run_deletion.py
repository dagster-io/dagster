"""cascade run deletion

Revision ID: 9fe9e746268c
Revises: da7cd32b690d
Create Date: 2020-02-10 18:13:58.993653

"""
from alembic import op
from sqlalchemy.engine import reflection

# pylint: disable=no-member

# revision identifiers, used by Alembic.
revision = "9fe9e746268c"
down_revision = "da7cd32b690d"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_context().bind
    inspector = reflection.Inspector.from_engine(bind)
    has_tables = inspector.get_table_names()

    if "runs" in has_tables and "run_tags" in has_tables:
        op.execute("delete from run_tags where run_id not in (select distinct run_id from runs);")


def downgrade():
    pass
