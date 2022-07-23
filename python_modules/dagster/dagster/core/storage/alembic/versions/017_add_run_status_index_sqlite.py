"""add run status index

Revision ID: 521d4caca7ad
Revises: 3e71cf573ba6
Create Date: 2021-02-23 15:55:33.837945

"""
from alembic import op
from sqlalchemy import inspect

# pylint: disable=no-member

# revision identifiers, used by Alembic.
revision = "521d4caca7ad"
down_revision = "3e71cf573ba6"
branch_labels = None
depends_on = None


def upgrade():
    inspector = inspect(op.get_bind())
    has_tables = inspector.get_table_names()
    if "runs" in has_tables:
        indices = [x.get("name") for x in inspector.get_indexes("runs")]
        if not "idx_run_status" in indices:
            op.create_index("idx_run_status", "runs", ["status"], unique=False)


def downgrade():
    inspector = inspect(op.get_bind())
    has_tables = inspector.get_table_names()
    if "runs" in has_tables:
        indices = [x.get("name") for x in inspector.get_indexes("runs")]
        if "idx_run_status" in indices:
            op.drop_index("idx_run_status", "runs")
