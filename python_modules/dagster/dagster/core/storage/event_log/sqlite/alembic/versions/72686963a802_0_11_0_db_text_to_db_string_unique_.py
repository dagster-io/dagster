"""0.11.0 db.Text to MySQLCompatabilityTypes.UniqueText for MySQL Support

Revision ID: 72686963a802
Revises: 6e1f65d78b92
Create Date: 2021-03-11 15:02:29.174707

"""
import sqlalchemy as sa
from alembic import op
from dagster.core.storage.migration.utils import has_table
from dagster.core.storage.sql import MySQLCompatabilityTypes

# pylint: disable=no-member

# revision identifiers, used by Alembic.
revision = "72686963a802"
down_revision = "6e1f65d78b92"
branch_labels = None
depends_on = None


def upgrade():
    if has_table("secondary_indexes"):
        with op.batch_alter_table("secondary_indexes") as batch_op:
            batch_op.alter_column(
                "name",
                type_=MySQLCompatabilityTypes.UniqueText,
                existing_type=sa.Text,
            )
    if has_table("asset_keys"):
        with op.batch_alter_table("asset_keys") as batch_op:
            batch_op.alter_column(
                "asset_key", type_=MySQLCompatabilityTypes.UniqueText, existing_type=sa.Text
            )


def downgrade():
    if has_table("secondary_indexes"):
        with op.batch_alter_table("secondary_indexes") as batch_op:
            batch_op.alter_column(
                "name",
                type_=sa.Text,
                existing_type=MySQLCompatabilityTypes.UniqueText,
            )
    if has_table("asset_keys"):
        with op.batch_alter_table("asset_keys") as batch_op:
            batch_op.alter_column(
                "asset_key",
                type_=sa.Text,
                existing_type=MySQLCompatabilityTypes.UniqueText,
            )
