"""add column last_observation_timestamp

Revision ID: 06bd7b15ca19
Revises: 29a8e9d74220
Create Date: 2022-01-18 21:22:49.337802

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import reflection


# revision identifiers, used by Alembic.
revision = '06bd7b15ca19'
down_revision = '29a8e9d74220'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_context().bind
    inspector = reflection.Inspector.from_engine(bind)
    has_tables = inspector.get_table_names()

    if "asset_keys" in has_tables:
        columns = [x.get("name") for x in inspector.get_columns("asset_keys")]
        with op.batch_alter_table("asset_keys") as batch_op:
            if "last_observation_timestamp" not in columns:
                batch_op.add_column(sa.Column("last_observation_timestamp", sa.TIMESTAMP))


def downgrade():
    bind = op.get_context().bind
    inspector = reflection.Inspector.from_engine(bind)
    has_tables = inspector.get_table_names()

    if "asset_keys" in has_tables:
        columns = [x.get("name") for x in inspector.get_columns("asset_keys")]
        with op.batch_alter_table("asset_keys") as batch_op:
            if "last_observation_timestamp" in columns:
                batch_op.drop_column("last_observation_timestamp")
