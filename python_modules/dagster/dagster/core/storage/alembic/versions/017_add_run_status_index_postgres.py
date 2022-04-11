"""add run status index

Revision ID: 3e71cf573ba6
Revises: 6d366a41b4be
Create Date: 2021-02-23 16:00:45.689578

"""
from alembic import op
from sqlalchemy.engine import reflection

# pylint: disable=no-member

# revision identifiers, used by Alembic.
revision = "3e71cf573ba6"
down_revision = "6d366a41b4be"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_context().bind
    inspector = reflection.Inspector.from_engine(bind)
    has_tables = inspector.get_table_names()
    if "runs" in has_tables:
        indices = [x.get("name") for x in inspector.get_indexes("runs")]
        if not "idx_run_status" in indices:
            op.create_index("idx_run_status", "runs", ["status"], unique=False)


def downgrade():
    bind = op.get_context().bind
    inspector = reflection.Inspector.from_engine(bind)
    has_tables = inspector.get_table_names()
    if "runs" in has_tables:
        indices = [x.get("name") for x in inspector.get_indexes("runs")]
        if "idx_run_status" in indices:
            op.drop_index("idx_run_status", "runs")
