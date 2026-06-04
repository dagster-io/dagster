from dagster._core.storage.runs.base import RunStorage as RunStorage

# NOTE (lightweight dagster): the SQLAlchemy-backed run storages below are
# imported lazily so the in-process `materialize()` path (which uses the
# stdlib-sqlite3 storage in dagster._core.storage.lightweight) does not require
# `sqlalchemy`/`alembic`. Install them via the `sql` extra to use these.

_LAZY_IMPORTS = {
    "InMemoryRunStorage": "dagster._core.storage.runs.in_memory",
    "DaemonHeartbeatsTable": "dagster._core.storage.runs.schema",
    "InstanceInfo": "dagster._core.storage.runs.schema",
    "RunStorageSqlMetadata": "dagster._core.storage.runs.schema",
    "SqlRunStorage": "dagster._core.storage.runs.sql_run_storage",
    "SqliteRunStorage": "dagster._core.storage.runs.sqlite",
}


def __getattr__(name: str):
    module_path = _LAZY_IMPORTS.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    import importlib

    return getattr(importlib.import_module(module_path), name)
