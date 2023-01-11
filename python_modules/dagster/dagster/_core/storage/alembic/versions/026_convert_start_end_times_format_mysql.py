"""convert start end times format.

Revision ID: 130b087bc274
Revises: b37316bf5584
Create Date: 2022-02-01 15:21:22.257972

"""
from alembic import op
from dagster._core.storage.migration.utils import (
    add_run_record_start_end_timestamps,
    drop_run_record_start_end_timestamps,
)

# revision identifiers, used by Alembic.
revision = "130b087bc274"
down_revision = "b37316bf5584"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.engine.name != "mysql":
        return

    drop_run_record_start_end_timestamps()
    add_run_record_start_end_timestamps()


def downgrade():
    pass
