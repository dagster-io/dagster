"""0.10.0 create new event log tables.

Revision ID: 942138e33bf9
Revises: a0234163e0e3
Create Date: 2021-01-13 12:54:27.921898

"""

from dagster._core.storage.migration.utils import create_0_10_0_event_log_tables

# revision identifiers, used by Alembic.
revision = "942138e33bf9"
down_revision = "a0234163e0e3"
branch_labels = None
depends_on = None


def upgrade():
    create_0_10_0_event_log_tables()


def downgrade():
    pass
