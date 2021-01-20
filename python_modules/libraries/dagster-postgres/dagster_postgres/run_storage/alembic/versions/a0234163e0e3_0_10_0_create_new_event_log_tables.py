"""0.10.0 create new event log tables

Revision ID: a0234163e0e3
Revises: 5ae53cd67d0c
Create Date: 2021-01-13 14:42:57.878627

"""
from dagster.core.storage.migration.utils import create_0_10_0_event_log_tables

# revision identifiers, used by Alembic.
revision = "a0234163e0e3"
down_revision = "5ae53cd67d0c"
branch_labels = None
depends_on = None


def upgrade():
    create_0_10_0_event_log_tables()


def downgrade():
    pass
