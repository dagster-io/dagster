"""add_run_tags_run_id_index

Revision ID: 284a732df317
Revises: 46b412388816
Create Date: 2024-07-10 09:35:20.215174

"""

from alembic import op
from dagster._core.storage.migration.utils import has_index, has_table

# revision identifiers, used by Alembic.
revision = "284a732df317"
down_revision = "46b412388816"
branch_labels = None
depends_on = None


def upgrade():
    if not has_table("run_tags"):
        return

    if not has_index("run_tags", "idx_run_tags_run_idx"):
        op.create_index(
            "idx_run_tags_run_idx",
            "run_tags",
            ["run_id", "id"],
            unique=False,
            postgresql_concurrently=True,
            mysql_length={"run_id": 255},
        )


def downgrade():
    if not has_table("run_tags"):
        return

    if has_index("run_tags", "idx_run_tags_run_idx"):
        op.drop_index(
            "idx_run_tags_run_idx",
            "run_tags",
            postgresql_concurrently=True,
        )
