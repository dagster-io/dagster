"""rebuild event log indices to include id.

Revision ID: a00dd8d936a1
Revises: 5e139331e376
Create Date: 2022-10-19 13:33:02.540229

"""

from dagster._core.storage.migration.utils import (
    add_id_based_event_indices,
    drop_id_based_event_indices,
)

# revision identifiers, used by Alembic.
revision = "a00dd8d936a1"
down_revision = "5e139331e376"
branch_labels = None
depends_on = None


def upgrade():
    add_id_based_event_indices()


def downgrade():
    drop_id_based_event_indices()
