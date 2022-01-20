"""add range index

Revision ID: 9c5f00e80ef2
Revises: 42add02bf976
Create Date: 2022-01-20 11:43:21.070463

"""
from alembic import op
from sqlalchemy.engine import reflection

# pylint: disable=no-member

# revision identifiers, used by Alembic.
revision = "9c5f00e80ef2"
down_revision = "42add02bf976"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_context().bind
    inspector = reflection.Inspector.from_engine(bind)
    has_tables = inspector.get_table_names()
    if "runs" in has_tables:
        indices = [x.get("name") for x in inspector.get_indexes("runs")]
        if not "idx_run_range" in indices:
            op.create_index(
                "idx_run_range",
                "runs",
                ["create_timestamp", "update_timestamp", "status"],
                unique=False,
            )


def downgrade():
    bind = op.get_context().bind
    inspector = reflection.Inspector.from_engine(bind)
    has_tables = inspector.get_table_names()
    if "runs" in has_tables:
        indices = [x.get("name") for x in inspector.get_indexes("runs")]
        if "idx_run_range" in indices:
            op.drop_index("idx_run_range", "runs")
