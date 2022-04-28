"""add_asset_key

Revision ID: c39c047fa021
Revises: 727ffe943a9f
Create Date: 2020-04-28 09:35:54.768791

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import reflection

# pylint: disable=no-member

# revision identifiers, used by Alembic.
revision = "c39c047fa021"
down_revision = "727ffe943a9f"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_context().bind
    inspector = reflection.Inspector.from_engine(bind)
    has_tables = inspector.get_table_names()
    if "event_logs" in has_tables:
        columns = [x.get("name") for x in inspector.get_columns("event_logs")]
        if "asset_key" not in columns:
            op.add_column("event_logs", sa.Column("asset_key", sa.String))
            op.create_index("idx_asset_key", "event_logs", ["asset_key"], unique=False)

            # also add index that was missing from the step_key migration
            op.create_index("idx_step_key", "event_logs", ["step_key"], unique=False)


def downgrade():
    bind = op.get_context().bind
    inspector = reflection.Inspector.from_engine(bind)
    has_tables = inspector.get_table_names()
    if "event_logs" in has_tables:
        columns = [x.get("name") for x in inspector.get_columns("event_logs")]
        if "asset_key" in columns:
            op.drop_column("event_logs", "asset_key")
            op.drop_index("idx_asset_key", "event_logs")

            # also drop the index that was missing from the step_key migration
            op.drop_index("idx_step_key", "event_logs")
