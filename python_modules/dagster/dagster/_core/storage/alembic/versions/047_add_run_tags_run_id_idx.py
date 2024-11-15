"""add run_id to run_tags index

Revision ID: 6b7fb194ff9c
Revises: 16e3655b4d9b
Create Date: 2024-11-14 22:19:46.456731

"""

from alembic import op
from dagster._core.storage.migration.utils import has_index, has_table

# revision identifiers, used by Alembic.
revision = "6b7fb194ff9c"
down_revision = "16e3655b4d9b"
branch_labels = None
depends_on = None


def upgrade():
    if has_table("run_tags"):
        if not has_index("run_tags", "idx_run_tags_run_id"):
            op.create_index(
                "idx_run_tags_run_id",
                "run_tags",
                ["key", "value", "run_id"],
                unique=True,
                postgresql_concurrently=True,
                mysql_length={"key": 64, "value": 64, "run_id": 255},
            )
        if has_index("run_tags", "idx_run_tags"):
            op.drop_index(
                "idx_run_tags",
                "run_tags",
                postgresql_concurrently=True,
            )


def downgrade():
    if has_table("run_tags"):
        if not has_index("run_tags", "idx_run_tags"):
            op.create_index(
                "idx_run_tags",
                "run_tags",
                ["key", "value"],
                unique=False,
                postgresql_concurrently=True,
                mysql_length={"key": 64, "value": 64},
            )
        if has_index("run_tags", "idx_run_tags_run_id"):
            op.drop_index(
                "idx_run_tags_run_id",
                "run_tags",
                postgresql_concurrently=True,
            )
