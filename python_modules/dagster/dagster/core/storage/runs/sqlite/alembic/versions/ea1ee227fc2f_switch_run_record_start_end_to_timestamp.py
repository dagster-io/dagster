"""switch run record start/end to timestamp

Revision ID: ea1ee227fc2f
Revises: b37316bf5584
Create Date: 2022-02-07 14:18:13.610262

"""
from dagster.core.storage.migration.utils import switch_to_start_timestamp_end_timestamp


# revision identifiers, used by Alembic.
revision = "ea1ee227fc2f"
down_revision = "b37316bf5584"
branch_labels = None
depends_on = None


def upgrade():
    switch_to_start_timestamp_end_timestamp()


def downgrade():
    pass
