import pytest
from dagster.utils.test.schedule_storage import TestScheduleStorage


class TestPostgresScheduleStorage(TestScheduleStorage):
    __test__ = True

    @pytest.fixture(scope="function", name="storage")
    def schedule_storage(self, clean_schedule_storage):  # pylint: disable=arguments-differ
        return clean_schedule_storage
