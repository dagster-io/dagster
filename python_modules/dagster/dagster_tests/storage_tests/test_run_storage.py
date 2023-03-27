import tempfile
from contextlib import contextmanager
from typing import Any, Mapping

import mock
import pytest
from dagster._core.storage.legacy_storage import LegacyRunStorage
from dagster._core.storage.runs import InMemoryRunStorage, SqliteRunStorage
from dagster._core.storage.sqlite_storage import DagsterSqliteStorage
from dagster._serdes.config_class import ConfigurableClassData
from typing_extensions import Self

from dagster_tests.storage_tests.utils.run_storage import TestRunStorage


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

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]
    ) -> Self:
        return NonBucketQuerySqliteRunStorage.from_local(inst_data=inst_data, **config_value)


@contextmanager
def create_in_memory_storage():
    yield InMemoryRunStorage()


@contextmanager
def create_legacy_run_storage():
    with tempfile.TemporaryDirectory() as tempdir:
        # first create the unified storage class
        storage = DagsterSqliteStorage.from_local(tempdir)
        # next create the legacy adapter class
        legacy_storage = LegacyRunStorage(storage)
        try:
            yield legacy_storage
        finally:
            storage.dispose()


class TestSqliteImplementation(TestRunStorage):
    __test__ = True

    @pytest.fixture(name="storage", params=[create_sqlite_run_storage])
    def run_storage(self, request):
        with request.param() as s:
            yield s

    def test_bucket_gating(self, storage):
        with mock.patch(
            "dagster._core.storage.runs.sqlite.sqlite_run_storage.get_sqlite_version",
            return_value="3.7.17",
        ):
            assert not storage.supports_bucket_queries

        with mock.patch(
            "dagster._core.storage.runs.sqlite.sqlite_run_storage.get_sqlite_version",
            return_value="3.25.1",
        ):
            assert storage.supports_bucket_queries

        with mock.patch(
            "dagster._core.storage.runs.sqlite.sqlite_run_storage.get_sqlite_version",
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


class TestLegacyStorage(TestRunStorage):
    __test__ = True

    @pytest.fixture(name="storage", params=[create_legacy_run_storage])
    def run_storage(self, request):
        with request.param() as s:
            yield s

    def test_storage_telemetry(self, storage):
        pass
