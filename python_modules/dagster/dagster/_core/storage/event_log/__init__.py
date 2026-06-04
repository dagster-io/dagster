from dagster._core.storage.event_log.base import (
    AssetRecord as AssetRecord,
    EventLogRecord as EventLogRecord,
    EventLogStorage as EventLogStorage,
)

# NOTE (lightweight dagster): the SQLAlchemy-backed storages below are imported
# lazily so that `import dagster` and the in-process `materialize()` path (which
# uses the stdlib-sqlite3 storage in dagster._core.storage.lightweight) do not
# require `sqlalchemy`/`alembic`. Accessing these names will import sqlalchemy;
# install it via the `sql` extra (`pip install dagster[sql]`).

_LAZY_IMPORTS = {
    "InMemoryEventLogStorage": "dagster._core.storage.event_log.in_memory",
    "SqlPollingEventWatcher": "dagster._core.storage.event_log.polling_event_watcher",
    "AssetKeyTable": "dagster._core.storage.event_log.schema",
    "DynamicPartitionsTable": "dagster._core.storage.event_log.schema",
    "SqlEventLogStorageMetadata": "dagster._core.storage.event_log.schema",
    "SqlEventLogStorageTable": "dagster._core.storage.event_log.schema",
    "SqlEventLogStorage": "dagster._core.storage.event_log.sql_event_log",
    "ConsolidatedSqliteEventLogStorage": "dagster._core.storage.event_log.sqlite",
    "SqliteEventLogStorage": "dagster._core.storage.event_log.sqlite",
}


def __getattr__(name: str):
    module_path = _LAZY_IMPORTS.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    import importlib

    return getattr(importlib.import_module(module_path), name)
