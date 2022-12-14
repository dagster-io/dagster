"""tick table update_timestamp index

Revision ID: abfa56354c9c
Revises: 6df03f4b1efb
Create Date: 2022-12-13 17:07:01.600453

"""
from alembic import op
import sqlalchemy as sa
from dagster._core.storage.migration.utils import create_tick_update_timestamp_index


# revision identifiers, used by Alembic.
revision = 'abfa56354c9c'
down_revision = '6df03f4b1efb'
branch_labels = None
depends_on = None


def upgrade():
    create_tick_update_timestamp_index()


def downgrade():
    pass
