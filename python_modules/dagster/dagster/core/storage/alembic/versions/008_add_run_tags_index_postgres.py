"""add run tags index

Revision ID: c9159e740d7e
Revises: c34498c29964
Create Date: 2020-12-01 12:19:34.460760

"""
from alembic import op
from sqlalchemy import inspect

# pylint: disable=no-member

# revision identifiers, used by Alembic.
revision = "c9159e740d7e"
down_revision = "c34498c29964"
branch_labels = None
depends_on = None


def upgrade():
    inspector = inspect(op.get_bind())
    has_tables = inspector.get_table_names()
    if "run_tags" in has_tables:
        indices = [x.get("name") for x in inspector.get_indexes("run_tags")]
        if not "idx_run_tags" in indices:
            op.create_index("idx_run_tags", "run_tags", ["key", "value"], unique=False)


def downgrade():
    inspector = inspect(op.get_bind())
    has_tables = inspector.get_table_names()
    if "run_tags" in has_tables:
        indices = [x.get("name") for x in inspector.get_indexes("run_tags")]
        if "idx_run_tags" in indices:
            op.drop_index("idx_run_tags", "run_tags")
