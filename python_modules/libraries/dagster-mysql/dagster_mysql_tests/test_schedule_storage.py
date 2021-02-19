import pytest
from dagster.utils.test.schedule_storage import TestScheduleStorage
from dagster_mysql.schedule_storage import MySQLScheduleStorage

TestScheduleStorage.__test__ = False


class TestMySQLScheduleStorage(TestScheduleStorage):
    __test__ = True

    @pytest.fixture(scope="function", name="storage")
    def schedule_storage(self, conn_string):  # pylint: disable=arguments-differ
        storage = MySQLScheduleStorage.create_clean_storage(conn_string)
        assert storage
        return storage
