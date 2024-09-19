"""create run_id idx.

Revision ID: c34498c29964
Revises: 07f83cc13695
Create Date: 2020-06-11 10:40:25.216776

"""

from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "c34498c29964"
down_revision = "07f83cc13695"
branch_labels = None
depends_on = None


def upgrade():
    inspector = inspect(op.get_bind())
    has_tables = inspector.get_table_names()
    if "event_logs" in has_tables:
        indices = [x.get("name") for x in inspector.get_indexes("event_logs")]
        if "idx_run_id" not in indices:
            op.create_index("idx_run_id", "event_logs", ["run_id"], unique=False)


def downgrade():
    inspector = inspect(op.get_bind())
    has_tables = inspector.get_table_names()
    if "event_logs" in has_tables:
        indices = [x.get("name") for x in inspector.get_indexes("event_logs")]
        if "idx_run_id" in indices:
            op.drop_index("idx_run_id", "event_logs")
