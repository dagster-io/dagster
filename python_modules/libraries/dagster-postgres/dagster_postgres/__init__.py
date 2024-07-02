from dagster._core.libraries import DagsterLibraryRegistry

from .storage import DagsterPostgresStorage
from .version import __version__
from .event_log import PostgresEventLogStorage
from .run_storage import PostgresRunStorage
from .schedule_storage import PostgresScheduleStorage

DagsterLibraryRegistry.register("dagster-postgres", __version__)
__all__ = [
    "DagsterPostgresStorage",
    "PostgresEventLogStorage",
    "PostgresRunStorage",
    "PostgresScheduleStorage",
]
