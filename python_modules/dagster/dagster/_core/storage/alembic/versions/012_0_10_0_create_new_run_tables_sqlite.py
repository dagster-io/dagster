"""0.10.0 create new run tables.

Revision ID: f5bac2c36fad
Revises: 5ae53cd67d0c
Create Date: 2021-01-13 10:48:24.022054

"""
from dagster._core.storage.migration.utils import create_0_10_0_run_tables

# revision identifiers, used by Alembic.
revision = "f5bac2c36fad"
down_revision = "5ae53cd67d0c"
branch_labels = None
depends_on = None


def upgrade():
    create_0_10_0_run_tables()


def downgrade():
    pass
