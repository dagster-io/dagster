from contextlib import contextmanager

import pytest
from dagster import seven
from dagster.core.storage.runs import InMemoryRunStorage, SqliteRunStorage
from dagster.utils.test.run_storage import TestRunStorage


@contextmanager
def create_sqlite_run_storage():
    with seven.TemporaryDirectory() as tempdir:
        yield SqliteRunStorage.from_local(tempdir)


@contextmanager
def create_in_memory_storage():
    yield InMemoryRunStorage()


TestRunStorage.__test__ = False


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
