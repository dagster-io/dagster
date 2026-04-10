from collections.abc import Iterator
from contextlib import contextmanager

from dagster._core.storage.event_log.sql_event_log import SqlEventLogStorage
from sqlalchemy.engine import Connection


class _CacheTestSqlEventLogStorage(SqlEventLogStorage):
    def __init__(self, support_getter) -> None:  # type: ignore[no-untyped-def]
        self._support_getter = support_getter

    @contextmanager
    def run_connection(self, run_id: str | None = None) -> Iterator[Connection]:
        raise NotImplementedError()
        yield

    @contextmanager
    def index_connection(self) -> Iterator[Connection]:
        raise NotImplementedError()
        yield

    def upgrade(self) -> None:
        raise NotImplementedError()

    def has_table(self, table_name: str) -> bool:
        raise NotImplementedError()

    def watch(self, run_id, cursor, callback):  # type: ignore[no-untyped-def]
        raise NotImplementedError()

    def end_watch(self, run_id, handler):  # type: ignore[no-untyped-def]
        raise NotImplementedError()

    def _get_dynamic_partition_display_label_col_support(self) -> bool:
        return self._support_getter()


def test_sql_event_log_storage_caches_positive_display_label_column_support():
    get_support_call_count = 0

    def _get_support():
        nonlocal get_support_call_count
        get_support_call_count += 1
        return True

    storage = _CacheTestSqlEventLogStorage(_get_support)

    assert storage.has_dynamic_partition_display_label_col() is True
    assert storage.has_dynamic_partition_display_label_col() is True
    assert storage.has_dynamic_partition_display_label_col() is True
    assert get_support_call_count == 1


def test_sql_event_log_storage_does_not_cache_missing_display_label_column_support():
    supports_display_labels = False
    get_support_call_count = 0

    def _get_support():
        nonlocal get_support_call_count
        get_support_call_count += 1
        return supports_display_labels

    storage = _CacheTestSqlEventLogStorage(_get_support)

    assert storage.has_dynamic_partition_display_label_col() is False

    supports_display_labels = True

    assert storage.has_dynamic_partition_display_label_col() is True
    assert get_support_call_count == 2
