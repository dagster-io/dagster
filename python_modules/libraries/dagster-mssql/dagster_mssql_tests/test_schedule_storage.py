import pytest
from dagster._utils.test.schedule_storage import TestScheduleStorage
from dagster_mssql.schedule_storage import MSSQLScheduleStorage

TestScheduleStorage.__test__ = False


class TestMSSQLScheduleStorage(TestScheduleStorage):
    __test__ = True

    @pytest.fixture(scope="function", name="storage")
    def schedule_storage(self, conn_string):
        storage = MSSQLScheduleStorage.create_clean_storage(conn_string)
        assert storage
        return storage
