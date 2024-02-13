from dagster._core.libraries import DagsterLibraryRegistry

from .event_log import PostgresEventLogStorage
from .run_storage import PostgresRunStorage
from .schedule_storage import PostgresScheduleStorage
from .storage import DagsterPostgresStorage
from .version import __version__

DagsterLibraryRegistry.register("dagster-postgres", __version__)
__all__ = [
    "DagsterPostgresStorage",
    "PostgresEventLogStorage",
    "PostgresRunStorage",
    "PostgresScheduleStorage",
]
