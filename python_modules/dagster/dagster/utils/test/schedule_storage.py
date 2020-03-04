import pytest

from dagster import DagsterInvariantViolationError, RepositoryDefinition
from dagster.core.scheduler import Schedule, ScheduleDefinitionData, ScheduleStatus


class TestScheduleStorage:
    '''
    You can extend this class to easily run these set of tests on any schedule storage. When extending,
    you simply need to override the `schedule_storage` fixture and return your implementation of
    `ScheduleStorage`.

    For example:

    ```
    TestScheduleStorage.__test__ = False

    class TestMyStorageImplementation(TestScheduleStorage):
        __test__ = True

        @pytest.fixture(scope='function', name='storage')
        def schedule_storage(self):  # pylint: disable=arguments-differ
            return MyStorageImplementation()
    ```
    '''

    @pytest.fixture(name='storage', params=[])
    def schedule_storage(self, request):
        with request.param() as s:
            yield s

    @staticmethod
    def build_schedule(
        schedule_name, cron_schedule, status=ScheduleStatus.STOPPED,
    ):
        return Schedule(ScheduleDefinitionData(schedule_name, cron_schedule), status, "", "",)

    def test_basic_schedule_storage(self, storage):
        assert storage

        repository = RepositoryDefinition("repository_name")
        schedule = self.build_schedule("my_schedule", "* * * * *")
        storage.add_schedule(repository, schedule)
        schedules = storage.all_schedules(repository)
        assert len(schedules) == 1

        schedule = schedules[0]
        assert schedule.name == "my_schedule"
        assert schedule.cron_schedule == "* * * * *"

    def test_add_multiple_schedules(self, storage):
        assert storage

        repository = RepositoryDefinition("repository_name")
        schedule = self.build_schedule("my_schedule", "* * * * *")
        schedule_2 = self.build_schedule("my_schedule_2", "* * * * *")
        schedule_3 = self.build_schedule("my_schedule_3", "* * * * *")

        storage.add_schedule(repository, schedule)
        storage.add_schedule(repository, schedule_2)
        storage.add_schedule(repository, schedule_3)

        schedules = storage.all_schedules(repository)
        assert len(schedules) == 3

        assert any(s.name == "my_schedule" for s in schedules)
        assert any(s.name == "my_schedule_2" for s in schedules)
        assert any(s.name == "my_schedule_3" for s in schedules)

    def test_get_schedule_by_name(self, storage):
        assert storage

        repository = RepositoryDefinition("repository_name")
        storage.add_schedule(repository, self.build_schedule("my_schedule", "* * * * *"))
        schedule = storage.get_schedule_by_name(repository, "my_schedule")

        assert schedule.name == "my_schedule"

    def test_get_schedule_by_name_not_found(self, storage):
        assert storage

        repository = RepositoryDefinition("repository_name")
        storage.add_schedule(repository, self.build_schedule("my_schedule", "* * * * *"))
        schedule = storage.get_schedule_by_name(repository, "fake_schedule")

        assert schedule is None

    def test_update_schedule(self, storage):
        assert storage

        repository = RepositoryDefinition("repository_name")
        schedule = self.build_schedule("my_schedule", "* * * * *")
        storage.add_schedule(repository, schedule)

        new_schedule = schedule.with_status(ScheduleStatus.RUNNING)
        storage.update_schedule(repository, new_schedule)

        schedules = storage.all_schedules(repository)
        assert len(schedules) == 1

        schedule = schedules[0]
        assert schedule.name == "my_schedule"
        assert schedule.status == ScheduleStatus.RUNNING

    def test_update_schedule_not_found(self, storage):
        assert storage

        repository = RepositoryDefinition("repository_name")
        schedule = self.build_schedule("my_schedule", "* * * * *")

        with pytest.raises(DagsterInvariantViolationError):
            storage.update_schedule(repository, schedule)

    def test_delete_schedule(self, storage):
        assert storage

        repository = RepositoryDefinition("repository_name")
        schedule = self.build_schedule("my_schedule", "* * * * *")
        storage.add_schedule(repository, schedule)
        storage.delete_schedule(repository, schedule)

        schedules = storage.all_schedules(repository)
        assert len(schedules) == 0

    def test_delete_schedule_not_found(self, storage):
        assert storage

        repository = RepositoryDefinition("repository_name")
        schedule = self.build_schedule("my_schedule", "* * * * *")

        with pytest.raises(DagsterInvariantViolationError):
            storage.delete_schedule(repository, schedule)

    def test_add_schedule_with_same_name(self, storage):
        assert storage

        repository = RepositoryDefinition("repository_name")
        schedule = self.build_schedule("my_schedule", "* * * * *")
        storage.add_schedule(repository, schedule)

        with pytest.raises(DagsterInvariantViolationError):
            storage.add_schedule(repository, schedule)
