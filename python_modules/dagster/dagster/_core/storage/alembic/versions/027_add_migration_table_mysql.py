"""add migration table

Revision ID: d538c9496c01
Revises: 130b087bc274
Create Date: 2022-03-23 13:00:19.789472

"""
from dagster.core.storage.migration.utils import create_schedule_secondary_index_table

# revision identifiers, used by Alembic.
revision = "d538c9496c01"
down_revision = "130b087bc274"
branch_labels = None
depends_on = None


def upgrade():
    create_schedule_secondary_index_table()


def downgrade():
    pass
