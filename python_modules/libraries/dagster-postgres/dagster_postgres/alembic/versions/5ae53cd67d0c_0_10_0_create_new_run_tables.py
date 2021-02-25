"""0.10.0 create new run tables

Revision ID: 5ae53cd67d0c
Revises: b32a4f3036d2
Create Date: 2021-01-13 14:42:51.215325

"""
from dagster.core.storage.migration.utils import create_0_10_0_run_tables

# revision identifiers, used by Alembic.
revision = "5ae53cd67d0c"
down_revision = "b32a4f3036d2"
branch_labels = None
depends_on = None


def upgrade():
    create_0_10_0_run_tables()


def downgrade():
    pass
