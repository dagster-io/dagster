import tempfile
from contextlib import contextmanager

import mock
import pytest

from dagster.core.storage.schedules import SqliteScheduleStorage
from dagster._utils.test.schedule_storage import TestScheduleStorage


@contextmanager
def create_sqlite_schedule_storage():
    with tempfile.TemporaryDirectory() as tempdir:
        yield SqliteScheduleStorage.from_local(tempdir)


class TestSqliteScheduleStorage(TestScheduleStorage):
    __test__ = True

    @pytest.fixture(name="storage", params=[create_sqlite_schedule_storage])
    def schedule_storage(self, request):
        with request.param() as s:
            yield s

    def test_bucket_gating(self, storage):
        with mock.patch(
            "dagster.core.storage.schedules.sqlite.sqlite_schedule_storage.get_sqlite_version",
            return_value="3.7.17",
        ):
            assert not storage.supports_batch_queries

        with mock.patch(
            "dagster.core.storage.schedules.sqlite.sqlite_schedule_storage.get_sqlite_version",
            return_value="3.25.1",
        ):
            assert storage.supports_batch_queries

        with mock.patch(
            "dagster.core.storage.schedules.sqlite.sqlite_schedule_storage.get_sqlite_version",
            return_value="3.25.19",
        ):
            assert storage.supports_batch_queries
