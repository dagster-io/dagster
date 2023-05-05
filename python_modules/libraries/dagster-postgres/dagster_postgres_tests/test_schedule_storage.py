import pytest
from dagster._utils.test.schedule_storage import TestScheduleStorage
from dagster_postgres.schedule_storage import PostgresScheduleStorage


class TestPostgresScheduleStorage(TestScheduleStorage):
    __test__ = True

    @pytest.fixture(scope="function", name="storage")
    def schedule_storage(self, conn_string):
        storage = PostgresScheduleStorage.create_clean_storage(conn_string)
        assert storage
        return storage
