"""0.10.0 create new schedule tables

Revision ID: 493871843165
Revises: a0234163e0e3
Create Date: 2021-01-13 14:43:03.678784

"""
from dagster.core.storage.migration.utils import create_0_10_0_schedule_tables

# revision identifiers, used by Alembic.
revision = "493871843165"
down_revision = "a0234163e0e3"
branch_labels = None
depends_on = None


def upgrade():
    create_0_10_0_schedule_tables()


def downgrade():
    pass
