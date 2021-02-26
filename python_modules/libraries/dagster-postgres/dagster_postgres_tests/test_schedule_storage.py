import pytest
from dagster.utils.test.schedule_storage import TestScheduleStorage
from dagster_postgres.schedule_storage import PostgresScheduleStorage


class TestPostgresScheduleStorage(TestScheduleStorage):
    __test__ = True

    @pytest.fixture(scope="function", name="storage")
    def schedule_storage(self, conn_string):  # pylint: disable=arguments-differ
        storage = PostgresScheduleStorage.create_clean_storage(conn_string)
        assert storage
        return storage
