"""add run tags index

Revision ID: 224640159acf
Revises: c63a27054f08
Create Date: 2020-12-01 12:10:23.650381

"""
from alembic import op
from sqlalchemy.engine import reflection

# pylint: disable=no-member

# revision identifiers, used by Alembic.
revision = "224640159acf"
down_revision = "c63a27054f08"
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
