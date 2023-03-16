"""cascade run deletion.

Revision ID: 8f8dba68fd3b
Revises: da7cd32b690d
Create Date: 2020-02-10 12:52:49.540462

"""
from alembic import op
from sqlalchemy import inspect

# alembic dynamically populates the alembic.context module

# revision identifiers, used by Alembic.
revision = "8f8dba68fd3b"
down_revision = "da7cd32b690d"
branch_labels = None
depends_on = None


def upgrade():
    inspector = inspect(op.get_bind())
    has_tables = inspector.get_table_names()

    if "runs" in has_tables and "run_tags" in has_tables:
        op.drop_constraint("run_tags_run_id_fkey", table_name="run_tags", type_="foreignkey")
        op.create_foreign_key(
            "run_tags_run_id_fkey",
            source_table="run_tags",
            referent_table="runs",
            local_cols=["run_id"],
            remote_cols=["run_id"],
            ondelete="CASCADE",
        )


def downgrade():
    inspector = inspect(op.get_bind())
    has_tables = inspector.get_table_names()

    if "runs" in has_tables and "run_tags" in has_tables:
        op.drop_constraint("run_tags_run_id_fkey", table_name="run_tags", type_="foreignkey")
        op.create_foreign_key(
            "run_tags_run_id_fkey",
            source_table="run_tags",
            referent_table="runs",
            local_cols=["run_id"],
            remote_cols=["run_id"],
        )
