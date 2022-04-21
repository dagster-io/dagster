import pytest
from dagster_postgres.schedule_storage import PostgresScheduleStorage

from dagster.utils.test.schedule_storage import TestScheduleStorage


class TestPostgresScheduleStorage(TestScheduleStorage):
    __test__ = True

    @pytest.fixture(scope="function", name="storage")
    def schedule_storage(self, conn_string):  # pylint: disable=arguments-renamed
        storage = PostgresScheduleStorage.create_clean_storage(conn_string)
        assert storage
        return storage
