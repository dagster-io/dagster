"""switch run record start/end to timestamp

Revision ID: 120468c8580f
Revises: 9c5f00e80ef2
Create Date: 2022-02-07 14:24:35.097313

"""
from dagster.core.storage.migration.utils import switch_to_start_timestamp_end_timestamp

# revision identifiers, used by Alembic.
revision = "120468c8580f"
down_revision = "9c5f00e80ef2"
branch_labels = None
depends_on = None


def upgrade():
    switch_to_start_timestamp_end_timestamp()


def downgrade():
    pass
