"""add index to job_ticks for latest lookups

Revision ID: 14e70fc5b610
Revises: 7e2f3204cf8e
Create Date: 2025-03-20 16:14:51.960683

"""
from alembic import op
from dagster._core.storage.migration.utils import has_index, has_table


# revision identifiers, used by Alembic.
revision = '14e70fc5b610'
down_revision = '7e2f3204cf8e'
branch_labels = None
depends_on = None


def upgrade():
    if has_table("job_ticks"):
        if not has_index("job_ticks", "idx_timestamp_origin_selector"):
            op.create_index(
                "idx_timestamp_origin_selector",
                "job_ticks",
                ["timestamp", "job_origin_id", "selector_id"],
                unique=False,
                mysql_length={"key": 64, "job_origin_id": 255, "selector_id": 255}
            )


def downgrade():
    if has_table("job_ticks"):
        if has_index("job_ticks", "idx_timestamp_origin_selector"):
            op.drop_index(
                "idx_timestamp_origin_selector",
                "job_ticks",
                if_exists=True
            )
