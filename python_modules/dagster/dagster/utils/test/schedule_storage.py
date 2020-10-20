import sys
import time

import pytest
from dagster import DagsterInvariantViolationError
from dagster.core.code_pointer import ModuleCodePointer
from dagster.core.origin import RepositoryPythonOrigin, SchedulePythonOrigin
from dagster.core.scheduler import ScheduleState, ScheduleStatus
from dagster.core.scheduler.scheduler import ScheduleTickData, ScheduleTickStatus
from dagster.seven import get_current_datetime_in_utc, get_timestamp_from_utc_datetime
from dagster.utils.error import SerializableErrorInfo


class TestScheduleStorage:
    """
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
    """

    @pytest.fixture(name="storage", params=[])
    def schedule_storage(self, request):
        with request.param() as s:
            yield s

    @staticmethod
    def fake_repo_target():
        return RepositoryPythonOrigin(sys.executable, ModuleCodePointer("fake", "fake"))

    @classmethod
    def build_schedule(
        cls, schedule_name, cron_schedule, status=ScheduleStatus.STOPPED,
    ):
        fake_target = SchedulePythonOrigin(schedule_name, cls.fake_repo_target())

        return ScheduleState(fake_target, status, cron_schedule, start_timestamp=None)

    def test_basic_schedule_storage(self, storage):
        assert storage

        schedule = self.build_schedule("my_schedule", "* * * * *")
        storage.add_schedule_state(schedule)
        schedules = storage.all_stored_schedule_state(self.fake_repo_target().get_id())
        assert len(schedules) == 1

        schedule = schedules[0]
        assert schedule.name == "my_schedule"
        assert schedule.cron_schedule == "* * * * *"
        assert schedule.start_timestamp == None

    def test_add_multiple_schedules(self, storage):
        assert storage

        schedule = self.build_schedule("my_schedule", "* * * * *")
        schedule_2 = self.build_schedule("my_schedule_2", "* * * * *")
        schedule_3 = self.build_schedule("my_schedule_3", "* * * * *")

        storage.add_schedule_state(schedule)
        storage.add_schedule_state(schedule_2)
        storage.add_schedule_state(schedule_3)

        schedules = storage.all_stored_schedule_state(self.fake_repo_target().get_id())
        assert len(schedules) == 3

        assert any(s.name == "my_schedule" for s in schedules)
        assert any(s.name == "my_schedule_2" for s in schedules)
        assert any(s.name == "my_schedule_3" for s in schedules)

    def test_get_schedule_state(self, storage):
        assert storage

        state = self.build_schedule("my_schedule", "* * * * *")
        storage.add_schedule_state(state)
        schedule = storage.get_schedule_state(state.schedule_origin_id)

        assert schedule.name == "my_schedule"
        assert schedule.start_timestamp == None

    def test_get_schedule_state_not_found(self, storage):
        assert storage

        storage.add_schedule_state(self.build_schedule("my_schedule", "* * * * *"))
        schedule = storage.get_schedule_state("fake_id")

        assert schedule is None

    def test_update_schedule(self, storage):
        assert storage

        schedule = self.build_schedule("my_schedule", "* * * * *")
        storage.add_schedule_state(schedule)

        now_time = get_current_datetime_in_utc()

        new_schedule = schedule.with_status(ScheduleStatus.RUNNING, start_time_utc=now_time)
        storage.update_schedule_state(new_schedule)

        schedules = storage.all_stored_schedule_state(self.fake_repo_target().get_id())
        assert len(schedules) == 1

        schedule = schedules[0]
        assert schedule.name == "my_schedule"
        assert schedule.status == ScheduleStatus.RUNNING
        assert schedule.start_timestamp == get_timestamp_from_utc_datetime(now_time)

        stopped_schedule = schedule.with_status(ScheduleStatus.STOPPED)
        storage.update_schedule_state(stopped_schedule)

        schedules = storage.all_stored_schedule_state(self.fake_repo_target().get_id())
        assert len(schedules) == 1

        schedule = schedules[0]
        assert schedule.name == "my_schedule"
        assert schedule.status == ScheduleStatus.STOPPED
        assert schedule.start_timestamp == None

    def test_update_schedule_not_found(self, storage):
        assert storage

        schedule = self.build_schedule("my_schedule", "* * * * *")

        with pytest.raises(DagsterInvariantViolationError):
            storage.update_schedule_state(schedule)

    def test_delete_schedule_state(self, storage):
        assert storage

        schedule = self.build_schedule("my_schedule", "* * * * *")
        storage.add_schedule_state(schedule)
        storage.delete_schedule_state(schedule.schedule_origin_id)

        schedules = storage.all_stored_schedule_state(self.fake_repo_target().get_id())
        assert len(schedules) == 0

    def test_delete_schedule_not_found(self, storage):
        assert storage

        schedule = self.build_schedule("my_schedule", "* * * * *")

        with pytest.raises(DagsterInvariantViolationError):
            storage.delete_schedule_state(schedule.schedule_origin_id)

    def test_add_schedule_with_same_name(self, storage):
        assert storage

        schedule = self.build_schedule("my_schedule", "* * * * *")
        storage.add_schedule_state(schedule)

        with pytest.raises(DagsterInvariantViolationError):
            storage.add_schedule_state(schedule)

    def build_tick(self, current_time, status=ScheduleTickStatus.STARTED, run_id=None, error=None):
        return ScheduleTickData(
            "my_schedule", "my_schedule", "* * * * *", current_time, status, run_id, error
        )

    def test_create_tick(self, storage):
        assert storage

        current_time = time.time()
        tick = storage.create_schedule_tick(self.build_tick(current_time))
        assert tick.tick_id == 1

        ticks = storage.get_schedule_ticks("my_schedule")
        assert len(ticks) == 1
        tick = ticks[0]
        assert tick.tick_id == 1
        assert tick.schedule_name == "my_schedule"
        assert tick.cron_schedule == "* * * * *"
        assert tick.timestamp == current_time
        assert tick.status == ScheduleTickStatus.STARTED
        assert tick.run_id == None
        assert tick.error == None

    def test_update_tick_to_success(self, storage):
        assert storage

        current_time = time.time()
        tick = storage.create_schedule_tick(self.build_tick(current_time))

        updated_tick = tick.with_status(ScheduleTickStatus.SUCCESS, run_id="1234")
        assert updated_tick.status == ScheduleTickStatus.SUCCESS

        storage.update_schedule_tick(updated_tick)

        ticks = storage.get_schedule_ticks("my_schedule")
        assert len(ticks) == 1
        tick = ticks[0]
        assert tick.tick_id == 1
        assert tick.schedule_name == "my_schedule"
        assert tick.cron_schedule == "* * * * *"
        assert tick.timestamp == current_time
        assert tick.status == ScheduleTickStatus.SUCCESS
        assert tick.run_id == "1234"
        assert tick.error == None

    def test_update_tick_to_skip(self, storage):
        assert storage

        current_time = time.time()
        tick = storage.create_schedule_tick(self.build_tick(current_time))

        updated_tick = tick.with_status(ScheduleTickStatus.SKIPPED)
        assert updated_tick.status == ScheduleTickStatus.SKIPPED

        storage.update_schedule_tick(updated_tick)

        ticks = storage.get_schedule_ticks("my_schedule")
        assert len(ticks) == 1
        tick = ticks[0]
        assert tick.tick_id == 1
        assert tick.schedule_name == "my_schedule"
        assert tick.cron_schedule == "* * * * *"
        assert tick.timestamp == current_time
        assert tick.status == ScheduleTickStatus.SKIPPED
        assert tick.run_id == None
        assert tick.error == None

    def test_update_tick_to_failure(self, storage):
        assert storage

        current_time = time.time()
        tick = storage.create_schedule_tick(self.build_tick(current_time))

        updated_tick = tick.with_status(
            ScheduleTickStatus.FAILURE,
            error=SerializableErrorInfo(message="Error", stack=[], cls_name="TestError"),
        )
        assert updated_tick.status == ScheduleTickStatus.FAILURE

        storage.update_schedule_tick(updated_tick)

        ticks = storage.get_schedule_ticks("my_schedule")
        assert len(ticks) == 1
        tick = ticks[0]
        assert tick.tick_id == 1
        assert tick.schedule_name == "my_schedule"
        assert tick.cron_schedule == "* * * * *"
        assert tick.timestamp == current_time
        assert tick.status == ScheduleTickStatus.FAILURE
        assert tick.run_id == None
        assert tick.error == SerializableErrorInfo(message="Error", stack=[], cls_name="TestError")

    def test_get_schedule_stats(self, storage):
        assert storage

        current_time = time.time()

        error = SerializableErrorInfo(message="Error", stack=[], cls_name="TestError")

        # Create ticks
        for x in range(2):
            storage.create_schedule_tick(self.build_tick(current_time))

        for x in range(3):
            storage.create_schedule_tick(
                self.build_tick(current_time, ScheduleTickStatus.SUCCESS, run_id=str(x)),
            )

        for x in range(4):
            storage.create_schedule_tick(self.build_tick(current_time, ScheduleTickStatus.SKIPPED),)

        for x in range(5):
            storage.create_schedule_tick(
                self.build_tick(current_time, ScheduleTickStatus.FAILURE, error=error),
            )

        stats = storage.get_schedule_tick_stats("my_schedule")
        assert stats.ticks_started == 2
        assert stats.ticks_succeeded == 3
        assert stats.ticks_skipped == 4
        assert stats.ticks_failed == 5
