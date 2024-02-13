import pytest
from dagster._utils.test.schedule_storage import TestScheduleStorage
from dagster_mysql.schedule_storage import MySQLScheduleStorage

TestScheduleStorage.__test__ = False


class TestMySQLScheduleStorage(TestScheduleStorage):
    __test__ = True

    @pytest.fixture(scope="function", name="storage")
    def schedule_storage(self, conn_string):
        storage = MySQLScheduleStorage.create_clean_storage(conn_string)
        assert storage
        return storage
