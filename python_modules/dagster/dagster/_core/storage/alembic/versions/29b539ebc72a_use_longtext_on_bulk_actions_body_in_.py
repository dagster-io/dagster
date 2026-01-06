"""use longtext on bulk_actions.body in mysql

Revision ID: 29b539ebc72a
Revises: f495c27d5019
Create Date: 2026-01-06 07:02:58.437749

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects.mysql import LONGTEXT

# revision identifiers, used by Alembic.
revision = "29b539ebc72a"
down_revision = "f495c27d5019"
branch_labels = None
depends_on = None


def upgrade():
    inspector = inspect(op.get_bind())
    if "mysql" not in inspector.dialect.dialect_description:
        return

    op.alter_column(
        table_name="bulk_actions",
        column_name="body",
        nullable=True,
        type_=sa.types.Text().with_variant(LONGTEXT, "mysql"),
        existing_type=sa.types.Text(),
    )


def downgrade():
    inspector = inspect(op.get_bind())
    if "mysql" not in inspector.dialect.dialect_description:
        return

    op.alter_column(
        table_name="bulk_actions",
        column_name="body",
        nullable=True,
        type_=sa.types.Text(),
        existing_type=sa.types.Text().with_variant(LONGTEXT, "mysql"),
    )
