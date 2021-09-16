"""add event log event type idx

Revision ID: 05844c702676
Revises: e784752027a6
Create Date: 2021-09-08 10:42:42.063814

"""
from dagster.core.storage.migration.utils import create_event_log_event_idx

# revision identifiers, used by Alembic.
revision = "05844c702676"
down_revision = "e784752027a6"
branch_labels = None
depends_on = None


def upgrade():
    create_event_log_event_idx()


def downgrade():
    pass
