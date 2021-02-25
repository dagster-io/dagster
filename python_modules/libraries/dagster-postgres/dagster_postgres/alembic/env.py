# pylint: disable=no-member
# alembic dynamically populates the alembic.context module

from logging.config import fileConfig

from alembic import context
from dagster.core.storage.event_log import SqlEventLogStorageMetadata
from dagster.core.storage.runs import SqlRunStorage
from dagster.core.storage.schedules import SqlScheduleStorage

config = context.config

fileConfig(config.config_file_name)

target_metadata = [SqlEventLogStorageMetadata, SqlRunStorage, SqlScheduleStorage]


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    connectable = config.attributes.get("connection", None)

    if connectable is None:
        raise Exception(
            "No connection set in alembic config. If you are trying to run this script from the "
            "command line, STOP and read the README."
        )

    context.configure(
        url=connectable.url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connection = config.attributes.get("connection", None)

    if connection is None:
        raise Exception(
            "No connection set in alembic config. If you are trying to run this script from the "
            "command line, STOP and read the README."
        )

    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
