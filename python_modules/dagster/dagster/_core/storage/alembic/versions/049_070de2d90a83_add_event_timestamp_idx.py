"""add event_logs.timestamp index

Revision ID: 070de2d90a83
Revises: 29b539ebc72a
Create Date: 2026-05-23 12:00:00.000000

"""

from alembic import op
from dagster._core.storage.migration.utils import has_index, has_table

# revision identifiers, used by Alembic.
revision = "070de2d90a83"
down_revision = "29b539ebc72a"
branch_labels = None
depends_on = None


def upgrade():
    if has_table("event_logs"):
        if not has_index("event_logs", "idx_event_timestamp"):
            op.create_index(
                "idx_event_timestamp",
                "event_logs",
                ["timestamp"],
                postgresql_concurrently=True,
            )


def downgrade():
    if has_table("event_logs"):
        if has_index("event_logs", "idx_event_timestamp"):
            op.drop_index(
                "idx_event_timestamp",
                "event_logs",
                postgresql_concurrently=True,
            )
