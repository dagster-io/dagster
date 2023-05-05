"""cascade run deletion.

Revision ID: 9fe9e746268c
Revises: 8f8dba68fd3b
Create Date: 2020-02-10 18:13:58.993653

"""
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "9fe9e746268c"
down_revision = "8f8dba68fd3b"
branch_labels = None
depends_on = None


def upgrade():
    inspector = inspect(op.get_bind())
    has_tables = inspector.get_table_names()

    if "runs" in has_tables and "run_tags" in has_tables:
        op.execute("delete from run_tags where run_id not in (select distinct run_id from runs);")


def downgrade():
    pass
