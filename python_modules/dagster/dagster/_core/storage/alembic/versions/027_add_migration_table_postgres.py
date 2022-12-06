"""add migration table.

Revision ID: 8d66aa722f94
Revises: d538c9496c01
Create Date: 2022-03-23 12:59:59.571272

"""
from dagster._core.storage.migration.utils import create_schedule_secondary_index_table

# revision identifiers, used by Alembic.
revision = "8d66aa722f94"
down_revision = "d538c9496c01"
branch_labels = None
depends_on = None


def upgrade():
    create_schedule_secondary_index_table()


def downgrade():
    pass
