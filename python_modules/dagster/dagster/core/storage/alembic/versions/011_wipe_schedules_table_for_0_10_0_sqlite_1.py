"""empty message

Revision ID: b22f16781a7c
Revises: b32a4f3036d2
Create Date: 2020-06-10 09:05:47.963960

"""
from alembic import op
from sqlalchemy.engine import reflection

from dagster.core.storage.migration.utils import get_currently_upgrading_instance, has_table

# alembic magic breaks pylint
# pylint: disable=no-member


# revision identifiers, used by Alembic.
revision = "b22f16781a7c"
down_revision = "b32a4f3036d2"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_context().bind

    inspector = reflection.Inspector.from_engine(bind)

    if "sqlite" not in inspector.dialect.dialect_description:
        return

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
