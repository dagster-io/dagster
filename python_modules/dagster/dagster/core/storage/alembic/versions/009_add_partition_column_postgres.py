"""add partition column

Revision ID: 3e0770016702
Revises: 224640159acf
Create Date: 2020-12-21 10:13:54.430623

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import reflection

# pylint: disable=no-member

# revision identifiers, used by Alembic.
revision = "3e0770016702"
down_revision = "224640159acf"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_context().bind
    inspector = reflection.Inspector.from_engine(bind)
    has_tables = inspector.get_table_names()
    if "event_logs" in has_tables:
        columns = [x.get("name") for x in inspector.get_columns("event_logs")]
        if "partition" not in columns:
            op.add_column("event_logs", sa.Column("partition", sa.String))
            op.create_index(
                "idx_asset_partition", "event_logs", ["asset_key", "partition"], unique=False
            )


def downgrade():
    bind = op.get_context().bind
    inspector = reflection.Inspector.from_engine(bind)
    has_tables = inspector.get_table_names()
    if "event_logs" in has_tables:
        columns = [x.get("name") for x in inspector.get_columns("event_logs")]
        if "partition" in columns:
            op.drop_column("event_logs", "partition")
            op.drop_index("idx_asset_partition", "event_logs")
