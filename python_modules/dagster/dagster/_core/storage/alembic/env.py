# pylint: disable=no-member
# alembic dynamically populates the alembic.context module

from alembic import context
from dagster._core.storage.event_log import SqlEventLogStorageMetadata
from dagster._core.storage.runs import SqlRunStorage
from dagster._core.storage.schedules import SqlScheduleStorage
from dagster._core.storage.sql import run_migrations_offline, run_migrations_online

config = context.config

target_metadata = [SqlEventLogStorageMetadata, SqlRunStorage, SqlScheduleStorage]

if context.is_offline_mode():
    run_migrations_offline(context, config, target_metadata)
else:
    run_migrations_online(context, config, target_metadata)
