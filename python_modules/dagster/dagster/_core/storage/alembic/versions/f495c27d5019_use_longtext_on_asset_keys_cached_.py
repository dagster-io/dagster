"""use longtext on asset_keys cached_status_data in mysql

Revision ID: f495c27d5019
Revises: 7e2f3204cf8e
Create Date: 2026-01-05 12:28:45.417971

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects.mysql import LONGTEXT

# revision identifiers, used by Alembic.
revision = "f495c27d5019"
down_revision = "7e2f3204cf8e"
branch_labels = None
depends_on = None


def upgrade():
    inspector = inspect(op.get_bind())
    if "mysql" not in inspector.dialect.dialect_description:
        return

    op.alter_column(
        table_name="asset_keys",
        column_name="cached_status_data",
        nullable=True,
        type_=sa.types.Text().with_variant(LONGTEXT, "mysql"),
        existing_type=sa.types.Text(),
    )


def downgrade():
    inspector = inspect(op.get_bind())
    if "mysql" not in inspector.dialect.dialect_description:
        return

    op.alter_column(
        table_name="asset_keys",
        column_name="cached_status_data",
        nullable=True,
        type_=sa.types.Text(),
        existing_type=sa.types.Text().with_variant(LONGTEXT, "mysql"),
    )
