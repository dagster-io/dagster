"""add run job index

Revision ID: 16689497301f
Revises: 6df03f4b1efb
Create Date: 2023-02-01 11:27:14.146322

"""
from dagster._core.storage.migration.utils import add_run_job_index, drop_run_job_index

# revision identifiers, used by Alembic.
revision = "16689497301f"
down_revision = "6df03f4b1efb"
branch_labels = None
depends_on = None


def upgrade():
    add_run_job_index()


def downgrade():
    drop_run_job_index()
