"""use longtext on job_ticks.tick_body and asset_daemon_asset_evaluations.asset_evaluation_body in mysql

Revision ID: 8e4a0968afe9
Revises: 29b539ebc72a
Create Date: 2026-01-09 16:53:34.657286

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects.mysql import LONGTEXT

# revision identifiers, used by Alembic.
revision = "8e4a0968afe9"
down_revision = "29b539ebc72a"
branch_labels = None
depends_on = None

COLUMNS = [
    ("job_ticks", "tick_body"),
    ("asset_daemon_asset_evaluations", "asset_evaluation_body"),
]


def upgrade():
    inspector = inspect(op.get_bind())
    if inspector.engine.dialect.name != "mysql":
        return

    for table_name, column_name in COLUMNS:
        op.alter_column(
            table_name=table_name,
            column_name=column_name,
            nullable=True,
            type_=sa.types.Text().with_variant(LONGTEXT, "mysql"),
            existing_type=sa.types.Text(),
        )


def downgrade():
    inspector = inspect(op.get_bind())
    if inspector.engine.dialect.name != "mysql":
        return

    for table_name, column_name in COLUMNS:
        op.alter_column(
            table_name=table_name,
            column_name=column_name,
            nullable=True,
            type_=sa.types.Text(),
            existing_type=sa.types.Text().with_variant(LONGTEXT, "mysql"),
        )
