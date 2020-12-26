import tempfile
from contextlib import contextmanager

import pytest
from dagster.core.storage.schedules import SqliteScheduleStorage
from dagster.utils.test.schedule_storage import TestScheduleStorage


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
