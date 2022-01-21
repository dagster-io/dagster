"""add range index

Revision ID: 17154c80d885
Revises: 29a8e9d74220
Create Date: 2022-01-20 11:45:26.092743

"""
from alembic import op
from sqlalchemy.engine import reflection

# pylint: disable=no-member

# revision identifiers, used by Alembic.
revision = "17154c80d885"
down_revision = "29a8e9d74220"
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
                mysql_length={
                    "create_timestamp": 8,
                    "update_timestamp": 8,
                    "status": 32,
                },
            )


def downgrade():
    bind = op.get_context().bind
    inspector = reflection.Inspector.from_engine(bind)
    has_tables = inspector.get_table_names()
    if "runs" in has_tables:
        indices = [x.get("name") for x in inspector.get_indexes("runs")]
        if "idx_run_range" in indices:
            op.drop_index("idx_run_range", "runs")
