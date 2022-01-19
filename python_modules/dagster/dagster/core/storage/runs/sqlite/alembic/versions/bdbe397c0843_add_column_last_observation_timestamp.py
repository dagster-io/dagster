"""add column last_observation_timestamp

Revision ID: bdbe397c0843
Revises: f4eed4c26e2c
Create Date: 2022-01-18 20:53:59.093876

"""
from alembic import op
import sqlalchemy as sa
from dagster.core.storage.migration.utils import has_column, has_table

# revision identifiers, used by Alembic.
revision = 'bdbe397c0843'
down_revision = 'f4eed4c26e2c'
branch_labels = None
depends_on = None


def upgrade():
    if has_table("asset_keys"):
        if not has_column("asset_keys", "last_observation_timestamp"):
            with op.batch_alter_table("asset_keys") as batch_op:
                batch_op.add_column(sa.Column("last_observation_timestamp", sa.TIMESTAMP))


def downgrade():
    if has_table("asset_keys"):
        if has_column("asset_keys", "last_observaiton_timestamp"):
            with op.batch_alter_table("asset_keys") as batch_op:
                batch_op.drop_column("last_observation_timestamp")
