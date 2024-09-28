import pytest

from dagster_tests.storage_tests.test_run_storage import (
    create_in_memory_storage,
    create_legacy_run_storage,
    create_sqlite_run_storage,
)
from dagster_tests.storage_tests.utils.daemon_cursor_storage import TestDaemonCursorStorage


class TestDaemonCursorStorages(TestDaemonCursorStorage):
    __test__ = True

    @pytest.fixture(
        name="storage",
        params=[
            create_in_memory_storage,
            create_sqlite_run_storage,
            create_legacy_run_storage,
        ],
    )
    def cursor_storage(self, request):
        with request.param() as s:
            yield s
