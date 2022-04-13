"""add migration table

Revision ID: 54666da3db5c
Revises: 0da417ae1b81
Create Date: 2022-03-23 12:58:43.144576

"""
from dagster.core.storage.migration.utils import create_schedule_secondary_index_table

# revision identifiers, used by Alembic.
revision = "54666da3db5c"
down_revision = "0da417ae1b81"
branch_labels = None
depends_on = None


def upgrade():
    create_schedule_secondary_index_table()


def downgrade():
    pass
