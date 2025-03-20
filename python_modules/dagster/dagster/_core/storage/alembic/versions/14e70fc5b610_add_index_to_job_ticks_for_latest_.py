"""add index to job_ticks for latest lookups

Revision ID: 14e70fc5b610
Revises: 7e2f3204cf8e
Create Date: 2025-03-20 16:14:51.960683

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '14e70fc5b610'
down_revision = '7e2f3204cf8e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "idx_origin_selector_timestamp",
        "job_ticks",
        ["timestamp", "job_origin_id", "selector_id"],
        unique=False
    )


def downgrade():
    op.drop_index(
        "idx_origin_selector_timestamp",
        "job_ticks",
        if_exists=True
    )
