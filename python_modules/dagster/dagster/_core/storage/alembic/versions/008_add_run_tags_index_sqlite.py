"""add run tags index.

Revision ID: 224640159acf
Revises: c9159e740d7e
Create Date: 2020-12-01 12:10:23.650381

"""
from alembic import op
from sqlalchemy import inspect

# pylint: disable=no-member

# revision identifiers, used by Alembic.
revision = "224640159acf"
down_revision = "c9159e740d7e"
branch_labels = None
depends_on = None


def upgrade():
    inspector = inspect(op.get_bind())
    has_tables = inspector.get_table_names()
    if "run_tags" in has_tables:
        indices = [x.get("name") for x in inspector.get_indexes("run_tags")]
        if "idx_run_tags" not in indices:
            op.create_index("idx_run_tags", "run_tags", ["key", "value"], unique=False)


def downgrade():
    inspector = inspect(op.get_bind())
    has_tables = inspector.get_table_names()
    if "run_tags" in has_tables:
        indices = [x.get("name") for x in inspector.get_indexes("run_tags")]
        if "idx_run_tags" in indices:
            op.drop_index("idx_run_tags", "run_tags")
