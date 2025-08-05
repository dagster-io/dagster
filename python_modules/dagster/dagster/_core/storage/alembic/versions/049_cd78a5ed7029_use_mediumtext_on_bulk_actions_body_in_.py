"""use mediumtext on bulk_actions body in mysql

Revision ID: cd78a5ed7029
Revises: b961dffeea1a
Create Date: 2025-08-05 13:35:53.147485

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.mysql import MEDIUMTEXT


# revision identifiers, used by Alembic.
revision = 'cd78a5ed7029'
down_revision = 'b961dffeea1a'
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
        type_=sa.types.Text().with_variant(MEDIUMTEXT, "mysql"),
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
        existing_type=sa.types.Text().with_variant(MEDIUMTEXT, "mysql"),
    )
