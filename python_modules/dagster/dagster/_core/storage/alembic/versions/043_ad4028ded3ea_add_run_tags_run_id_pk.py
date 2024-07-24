"""add run tags run id pk

Revision ID: 043_ad4028ded3ea
Revises: 46b412388816
Create Date: 2024-07-10 10:44:15.477787

"""

import sqlalchemy as db
from alembic import op
from dagster._core.storage.migration.utils import has_column, has_table
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = "043_ad4028ded3ea"
down_revision = "46b412388816"
branch_labels = None
depends_on = None


def upgrade():
    if not has_table("runs"):
        return

    if not has_column("run_tags", "run_id_pk"):
        op.add_column(
            "run_tags",
            db.Column(
                "run_id_pk", db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"), nullable=True
            ),
        )


def downgrade():
    if not has_table("runs"):
        return

    if has_column("run_tags", "run_id_pk"):
        op.drop_column("run_tags", "run_id_pk")
