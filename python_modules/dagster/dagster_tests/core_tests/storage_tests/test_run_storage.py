import tempfile
from contextlib import contextmanager

import pytest
from dagster.core.storage.runs import InMemoryRunStorage, SqliteRunStorage
from dagster_tests.core_tests.storage_tests.utils.run_storage import TestRunStorage


@contextmanager
def create_sqlite_run_storage():
    with tempfile.TemporaryDirectory() as tempdir:
        yield SqliteRunStorage.from_local(tempdir)


@contextmanager
def create_in_memory_storage():
    yield InMemoryRunStorage()


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
