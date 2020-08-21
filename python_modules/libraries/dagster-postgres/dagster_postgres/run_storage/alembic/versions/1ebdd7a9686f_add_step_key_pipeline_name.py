"""add step_key pipeline_name

Revision ID: 1ebdd7a9686f
Revises: 8f8dba68fd3b
Create Date: 2020-03-31 11:21:26.811734

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import reflection

# pylint: disable=no-member

# revision identifiers, used by Alembic.
revision = "1ebdd7a9686f"
down_revision = "8f8dba68fd3b"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_context().bind
    inspector = reflection.Inspector.from_engine(bind)
    has_tables = inspector.get_table_names()
    if "event_logs" in has_tables:
        columns = [x.get("name") for x in inspector.get_columns("event_logs")]
        if "step_key" not in columns:
            op.add_column("event_logs", sa.Column("step_key", sa.String))


def downgrade():
    bind = op.get_context().bind
    inspector = reflection.Inspector.from_engine(bind)
    has_tables = inspector.get_table_names()
    if "event_logs" in has_tables:
        columns = [x.get("name") for x in inspector.get_columns("event_logs")]
        if "step_key" in columns:
            op.drop_column("event_logs", "step_key")
