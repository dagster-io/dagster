"""add event log event type idx.

Revision ID: f4b6a4885876
Revises: 29a8e9d74220
Create Date: 2021-09-08 10:28:28.730620

"""

from dagster._core.storage.migration.utils import create_event_log_event_idx

# revision identifiers, used by Alembic.
revision = "f4b6a4885876"
down_revision = "29a8e9d74220"
branch_labels = None
depends_on = None


def upgrade():
    create_event_log_event_idx()


def downgrade():
    pass
