"""0.10.0 create new schedule tables.

Revision ID: 8ccbed5060b8
Revises: 493871843165
Create Date: 2021-01-13 12:56:41.971500

"""

from dagster._core.storage.migration.utils import create_0_10_0_schedule_tables

# revision identifiers, used by Alembic.
revision = "8ccbed5060b8"
down_revision = "493871843165"
branch_labels = None
depends_on = None


def upgrade():
    create_0_10_0_schedule_tables()


def downgrade():
    pass
