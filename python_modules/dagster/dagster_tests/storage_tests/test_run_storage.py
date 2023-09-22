import tempfile
from contextlib import contextmanager

import pytest
from dagster._core.storage.legacy_storage import LegacyRunStorage
from dagster._core.storage.runs import InMemoryRunStorage, SqliteRunStorage
from dagster._core.storage.sqlite_storage import DagsterSqliteStorage

from dagster_tests.storage_tests.utils.run_storage import TestRunStorage


@contextmanager
def create_sqlite_run_storage():
    with tempfile.TemporaryDirectory() as tempdir:
        yield SqliteRunStorage.from_local(tempdir)


@contextmanager
def create_in_memory_storage():
    storage = InMemoryRunStorage()
    try:
        yield storage
    finally:
        storage.dispose()


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
