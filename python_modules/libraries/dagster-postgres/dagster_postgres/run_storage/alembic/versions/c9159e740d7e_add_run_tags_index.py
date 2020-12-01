"""add run tags index

Revision ID: c9159e740d7e
Revises: 07f83cc13695
Create Date: 2020-12-01 12:19:34.460760

"""
from alembic import op
from sqlalchemy.engine import reflection

# pylint: disable=no-member

# revision identifiers, used by Alembic.
revision = "c9159e740d7e"
down_revision = "07f83cc13695"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_context().bind
    inspector = reflection.Inspector.from_engine(bind)
    has_tables = inspector.get_table_names()
    if "run_tags" in has_tables:
        indices = [x.get("name") for x in inspector.get_indexes("run_tags")]
        if not "idx_run_tags" in indices:
            op.create_index("idx_run_tags", "run_tags", ["key", "value"], unique=False)


def downgrade():
    bind = op.get_context().bind
    inspector = reflection.Inspector.from_engine(bind)
    has_tables = inspector.get_table_names()
    if "run_tags" in has_tables:
        indices = [x.get("name") for x in inspector.get_indexes("run_tags")]
        if "idx_run_tags" in indices:
            op.drop_index("idx_run_tags", "run_tags")
