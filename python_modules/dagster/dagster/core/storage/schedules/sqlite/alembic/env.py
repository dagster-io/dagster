# pylint: disable=no-member
# alembic dynamically populates the alembic.context module

from alembic import context
from dagster.core.storage.schedules import ScheduleStorageSqlMetadata
from dagster.core.storage.sqlite import run_migrations_offline, run_migrations_online

config = context.config

target_metadata = ScheduleStorageSqlMetadata

if context.is_offline_mode():
    run_migrations_offline(context, config, target_metadata)
else:
    run_migrations_online(context, config, target_metadata)
