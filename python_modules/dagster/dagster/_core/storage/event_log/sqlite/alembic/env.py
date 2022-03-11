# pylint: disable=no-member
# alembic dynamically populates the alembic.context module

from alembic import context

from dagster._core.storage.event_log import SqlEventLogStorageMetadata
from dagster._core.storage.sqlite import run_migrations_offline, run_migrations_online

config = context.config

target_metadata = SqlEventLogStorageMetadata

if context.is_offline_mode():
    run_migrations_offline(context, config, target_metadata)
else:
    run_migrations_online(context, config, target_metadata)
