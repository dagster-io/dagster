"""wipe schedules table for 0.10.0

Revision ID: b32a4f3036d2
Revises: f3e43ff66603
Create Date: 2021-01-11 22:20:01.253271

"""
from alembic import op
from dagster.core.storage.migration.utils import get_currently_upgrading_instance, has_table

# alembic magic breaks pylint
# pylint: disable=no-member


# revision identifiers, used by Alembic.
revision = "b32a4f3036d2"
down_revision = "f3e43ff66603"
branch_labels = None
depends_on = None


def upgrade():
    instance = get_currently_upgrading_instance()
    if instance.scheduler:
        instance.scheduler.wipe(instance)

    #   No longer dropping the "schedules" table here, since
    #   the 0.10.0 migration checks for the presence of the "schedules"
    #   table during the migration from the "schedules" table to the "jobs"
    #   table - see create_0_10_0_schedule_ tables
    #   if has_table("schedules"):
    #       op.drop_table("schedules")

    if has_table("schedule_ticks"):
        op.drop_table("schedule_ticks")


def downgrade():
    pass
