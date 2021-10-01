"""add event log event type idx

Revision ID: 29a8e9d74220
Revises: 1a2d72f6b24e
Create Date: 2021-09-08 10:29:08.823969

"""
from dagster.core.storage.migration.utils import create_event_log_event_idx

# revision identifiers, used by Alembic.
revision = "29a8e9d74220"
down_revision = "1a2d72f6b24e"
branch_labels = None
depends_on = None


def upgrade():
    create_event_log_event_idx()


def downgrade():
    pass
