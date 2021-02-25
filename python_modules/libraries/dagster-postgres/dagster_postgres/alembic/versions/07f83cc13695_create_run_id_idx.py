"""create run_id idx

Revision ID: 07f83cc13695
Revises: 5c18fd3c2957
Create Date: 2020-06-11 09:27:11.922143

"""
from alembic import op
from sqlalchemy.engine import reflection

# pylint: disable=no-member

# revision identifiers, used by Alembic.
revision = "07f83cc13695"
down_revision = "5c18fd3c2957"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_context().bind
    inspector = reflection.Inspector.from_engine(bind)
    has_tables = inspector.get_table_names()
    if "event_logs" in has_tables:
        indices = [x.get("name") for x in inspector.get_indexes("event_logs")]
        if not "idx_run_id" in indices:
            op.create_index("idx_run_id", "event_logs", ["run_id"], unique=False)


def downgrade():
    bind = op.get_context().bind
    inspector = reflection.Inspector.from_engine(bind)
    has_tables = inspector.get_table_names()
    if "event_logs" in has_tables:
        indices = [x.get("name") for x in inspector.get_indexes("event_logs")]
        if "idx_run_id" in indices:
            op.drop_index("idx_run_id", "event_logs")
