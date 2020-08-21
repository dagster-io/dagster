"""scheduler update

Revision ID: 5c18fd3c2957
Revises: 727ffe943a9f
Create Date: 2020-06-10 10:00:57.793622

"""
from alembic import op

from dagster.core.storage.migration.utils import get_currently_upgrading_instance, has_table

# alembic magic breaks pylint
# pylint: disable=no-member


# revision identifiers, used by Alembic.
revision = "5c18fd3c2957"
down_revision = "727ffe943a9f"
branch_labels = None
depends_on = None


def upgrade():
    instance = get_currently_upgrading_instance()
    if instance.scheduler:
        instance.scheduler.wipe(instance)

    if has_table("schedules"):
        op.drop_table("schedules")

    if has_table("schedule_ticks"):
        op.drop_table("schedule_ticks")


def downgrade():
    if has_table("schedules"):
        op.drop_table("schedules")

    if has_table("schedule_ticks"):
        op.drop_table("schedule_ticks")
