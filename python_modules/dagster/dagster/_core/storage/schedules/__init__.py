from dagster._core.storage.schedules.base import ScheduleStorage as ScheduleStorage

# NOTE (lightweight dagster): SQLAlchemy-backed schedule storages imported lazily
# so the in-process execution path does not require sqlalchemy/alembic.

_LAZY_IMPORTS = {
    "ScheduleStorageSqlMetadata": "dagster._core.storage.schedules.schema",
    "SqlScheduleStorage": "dagster._core.storage.schedules.sql_schedule_storage",
    "SqliteScheduleStorage": "dagster._core.storage.schedules.sqlite",
}


def __getattr__(name: str):
    module_path = _LAZY_IMPORTS.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    import importlib

    return getattr(importlib.import_module(module_path), name)
