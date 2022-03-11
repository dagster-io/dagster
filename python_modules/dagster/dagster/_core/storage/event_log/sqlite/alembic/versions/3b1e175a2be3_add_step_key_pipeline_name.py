"""add step_key pipeline_name

Revision ID: 3b1e175a2be3
Revises: 567bc23fd1ac
Create Date: 2020-03-31 11:01:42.609069

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import reflection

# pylint: disable=no-member

# revision identifiers, used by Alembic.
revision = "3b1e175a2be3"
down_revision = "567bc23fd1ac"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_context().bind
    inspector = reflection.Inspector.from_engine(bind)
    has_tables = inspector.get_table_names()
    if "event_logs" in has_tables:
        op.add_column("event_logs", sa.Column("step_key", sa.String))


def downgrade():
    bind = op.get_context().bind
    inspector = reflection.Inspector.from_engine(bind)
    has_tables = inspector.get_table_names()
    if "event_logs" in has_tables:
        op.drop_column("event_logs", "step_key")
