import tempfile
from contextlib import contextmanager

import mock
import pytest
from dagster_tests.core_tests.storage_tests.utils.run_storage import TestRunStorage

from dagster.core.storage.runs import InMemoryRunStorage, SqliteRunStorage


@contextmanager
def create_sqlite_run_storage():
    with tempfile.TemporaryDirectory() as tempdir:
        yield SqliteRunStorage.from_local(tempdir)


@contextmanager
def create_non_bucket_sqlite_run_storage():
    with tempfile.TemporaryDirectory() as tempdir:
        yield NonBucketQuerySqliteRunStorage.from_local(tempdir)


class NonBucketQuerySqliteRunStorage(SqliteRunStorage):
    @property
    def supports_bucket_queries(self):
        return False

    @staticmethod
    def from_config_value(inst_data, config_value):
        return NonBucketQuerySqliteRunStorage.from_local(inst_data=inst_data, **config_value)


@contextmanager
def create_in_memory_storage():
    yield InMemoryRunStorage()


class TestSqliteImplementation(TestRunStorage):
    __test__ = True

    @pytest.fixture(name="storage", params=[create_sqlite_run_storage])
    def run_storage(self, request):
        with request.param() as s:
            yield s

    def test_bucket_gating(self, storage):
        with mock.patch(
            "dagster.core.storage.runs.sqlite.sqlite_run_storage.get_sqlite_version",
            return_value="3.7.17",
        ):
            assert not storage.supports_bucket_queries

        with mock.patch(
            "dagster.core.storage.runs.sqlite.sqlite_run_storage.get_sqlite_version",
            return_value="3.25.1",
        ):
            assert storage.supports_bucket_queries

        with mock.patch(
            "dagster.core.storage.runs.sqlite.sqlite_run_storage.get_sqlite_version",
            return_value="3.25.19",
        ):
            assert storage.supports_bucket_queries


class TestNonBucketQuerySqliteImplementation(TestRunStorage):
    __test__ = True

    @pytest.fixture(name="storage", params=[create_non_bucket_sqlite_run_storage])
    def run_storage(self, request):
        with request.param() as s:
            yield s


class TestInMemoryImplementation(TestRunStorage):
    __test__ = True

    @pytest.fixture(name="storage", params=[create_in_memory_storage])
    def run_storage(self, request):
        with request.param() as s:
            yield s

    def test_storage_telemetry(self, storage):
        pass
