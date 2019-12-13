# pylint: disable=no-member
# alembic dynamically populates the alembic.context module

from logging.config import fileConfig

from alembic import context

from dagster.core.storage.event_log import SqlEventLogStorageMetadata
from dagster.core.storage.sql import run_migrations_offline, run_migrations_online

config = context.config

fileConfig(config.config_file_name)

target_metadata = SqlEventLogStorageMetadata

if context.is_offline_mode():
    run_migrations_offline(context, config, target_metadata)
else:
    run_migrations_online(context, config, target_metadata)
