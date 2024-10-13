import pytest
from dagster._core.test_utils import ensure_dagster_tests_import
from dagster_postgres.run_storage import PostgresRunStorage

ensure_dagster_tests_import()
from dagster_tests.storage_tests.utils.daemon_cursor_storage import TestDaemonCursorStorage


class TestPostgresDaemonCursorStorage(TestDaemonCursorStorage):
    __test__ = True

    @pytest.fixture(scope="function", name="storage")
    def cursor_storage(self, conn_string):
        storage = PostgresRunStorage.create_clean_storage(conn_string)
        assert storage
        return storage
