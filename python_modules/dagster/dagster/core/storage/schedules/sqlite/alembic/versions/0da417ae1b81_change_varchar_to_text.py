"""change varchar to text

Revision ID: 0da417ae1b81
Revises: 8ccbed5060b8
Create Date: 2021-01-14 12:29:33.410870

"""
import sqlalchemy as sa
from alembic import op
from dagster.core.storage.migration.utils import has_table

# pylint: disable=no-member

# revision identifiers, used by Alembic.
revision = "0da417ae1b81"
down_revision = "8ccbed5060b8"
branch_labels = None
depends_on = None


def upgrade():
    if has_table("jobs"):
        with op.batch_alter_table("jobs") as batch_op:
            batch_op.alter_column("job_body", type_=sa.Text, existing_type=sa.String)

    if has_table("job_ticks"):
        with op.batch_alter_table("job_ticks") as batch_op:
            batch_op.alter_column(
                "tick_body",
                type_=sa.Text,
                existing_type=sa.String,
            )


def downgrade():
    if has_table("jobs"):
        with op.batch_alter_table("jobs") as batch_op:
            batch_op.alter_column("job_body", type_=sa.String, existing_type=sa.Text)

    if has_table("job_ticks"):
        with op.batch_alter_table("job_ticks") as batch_op:
            batch_op.alter_column(
                "tick_body",
                type_=sa.String,
                existing_type=sa.Text,
            )
