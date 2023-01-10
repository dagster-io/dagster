"""add_columns_start_time_and_end_time.

Revision ID: f78059038d01
Revises: 05844c702676
Create Date: 2022-01-25 09:26:35.820814

"""
from dagster._core.storage.migration.utils import (
    add_run_record_start_end_timestamps,
    drop_run_record_start_end_timestamps,
)

# revision identifiers, used by Alembic.
revision = "f78059038d01"
down_revision = "05844c702676"
branch_labels = None
depends_on = None

# pylint: disable=no-member


def upgrade():
    add_run_record_start_end_timestamps()


def downgrade():
    drop_run_record_start_end_timestamps()
