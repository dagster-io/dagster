"""add event log event type idx

Revision ID: 29a8e9d74220
Revises: e784752027a6
Create Date: 2021-09-08 10:29:08.823969

"""
from dagster.core.storage.migration.utils import create_event_log_event_idx

# revision identifiers, used by Alembic.
revision = "29a8e9d74220"
down_revision = "e784752027a6"
branch_labels = None
depends_on = None


def upgrade():
    create_event_log_event_idx()


def downgrade():
    pass
