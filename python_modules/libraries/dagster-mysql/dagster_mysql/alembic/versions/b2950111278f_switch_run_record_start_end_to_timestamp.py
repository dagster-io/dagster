"""switch run record start/end to timestamp

Revision ID: b2950111278f
Revises: 17154c80d885
Create Date: 2022-02-07 14:26:22.473920

"""
from dagster.core.storage.migration.utils import switch_to_start_timestamp_end_timestamp


# revision identifiers, used by Alembic.
revision = "b2950111278f"
down_revision = "17154c80d885"
branch_labels = None
depends_on = None


def upgrade():
    switch_to_start_timestamp_end_timestamp()


def downgrade():
    pass
