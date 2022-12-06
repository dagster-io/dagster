"""add instigators table.

Revision ID: 16e3115a602a
Revises: 5b467f7af3f6
Create Date: 2022-03-18 16:17:06.516027

"""
from dagster._core.storage.migration.utils import create_instigators_table

# revision identifiers, used by Alembic.
revision = "16e3115a602a"
down_revision = "5b467f7af3f6"
branch_labels = None
depends_on = None


def upgrade():
    create_instigators_table()


def downgrade():
    pass
