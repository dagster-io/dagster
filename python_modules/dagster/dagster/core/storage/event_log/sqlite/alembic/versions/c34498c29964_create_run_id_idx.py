"""create run_id idx

Revision ID: c34498c29964
Revises: c39c047fa021
Create Date: 2020-06-11 10:40:25.216776

"""
from alembic import op
from sqlalchemy.engine import reflection

# pylint: disable=no-member

# revision identifiers, used by Alembic.
revision = "c34498c29964"
down_revision = "c39c047fa021"
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
