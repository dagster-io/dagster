"""add column last_observation_timestamp

Revision ID: 9642811d99b1
Revises: 05844c702676
Create Date: 2022-01-19 11:14:54.048737

"""
from alembic import op
import sqlalchemy as sa
from dagster.core.storage.migration.utils import has_column, has_table

# revision identifiers, used by Alembic.
revision = '9642811d99b1'
down_revision = '05844c702676'
branch_labels = None
depends_on = None


def upgrade():
    if has_table("asset_keys"):
        if not has_column("asset_keys", "last_observation_timestamp"):
            with op.batch_alter_table("asset_keys") as batch_op:
                batch_op.add_column(sa.Column("last_observation_timestamp", sa.TIMESTAMP))


def downgrade():
    if has_table("asset_keys"):
        if has_column("asset_keys", "last_observation_timestamp"):
            with op.batch_alter_table("asset_keys") as batch_op:
                batch_op.drop_column("last_observation_timestamp")
