import tempfile
from contextlib import contextmanager

import mock
import pytest
from dagster._core.storage.legacy_storage import LegacyScheduleStorage
from dagster._core.storage.schedules import SqliteScheduleStorage
from dagster._core.storage.sqlite_storage import DagsterSqliteStorage
from dagster._utils.test.schedule_storage import TestScheduleStorage


@contextmanager
def create_sqlite_schedule_storage():
    with tempfile.TemporaryDirectory() as tempdir:
        yield SqliteScheduleStorage.from_local(tempdir)


@contextmanager
def create_legacy_schedule_storage():
    with tempfile.TemporaryDirectory() as tempdir:
        # first create the unified storage class
        storage = DagsterSqliteStorage.from_local(tempdir)
        # next create the legacy adapter class
        legacy_storage = LegacyScheduleStorage(storage)
        try:
            yield legacy_storage
        finally:
            legacy_storage.dispose()
            storage.dispose()


class TestSqliteScheduleStorage(TestScheduleStorage):
    __test__ = True

    @pytest.fixture(name="storage", params=[create_sqlite_schedule_storage])
    def schedule_storage(self, request):
        with request.param() as s:
            yield s

    def test_bucket_gating(self, storage):
        with mock.patch(
            "dagster._core.storage.schedules.sqlite.sqlite_schedule_storage.get_sqlite_version",
            return_value="3.7.17",
        ):
            assert not storage.supports_batch_queries

        with mock.patch(
            "dagster._core.storage.schedules.sqlite.sqlite_schedule_storage.get_sqlite_version",
            return_value="3.25.1",
        ):
            assert storage.supports_batch_queries

        with mock.patch(
            "dagster._core.storage.schedules.sqlite.sqlite_schedule_storage.get_sqlite_version",
            return_value="3.25.19",
        ):
            assert storage.supports_batch_queries


class TestLegacyStorage(TestScheduleStorage):
    __test__ = True

    @pytest.fixture(name="storage", params=[create_legacy_schedule_storage])
    def schedule_storage(self, request):
        with request.param() as s:
            yield s
