from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_postgres.event_log import PostgresEventLogStorage
from dagster_postgres.run_storage import PostgresRunStorage
from dagster_postgres.schedule_storage import PostgresScheduleStorage
from dagster_postgres.storage import DagsterPostgresStorage
from dagster_postgres.version import __version__

DagsterLibraryRegistry.register("dagster-postgres", __version__)
__all__ = [
    "DagsterPostgresStorage",
    "PostgresEventLogStorage",
    "PostgresRunStorage",
    "PostgresScheduleStorage",
]
