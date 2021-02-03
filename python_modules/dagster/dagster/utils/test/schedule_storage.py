import re
import sys
import time

import pendulum
import pytest
from dagster import DagsterInvariantViolationError
from dagster.core.errors import DagsterScheduleWipeRequired
from dagster.core.host_representation import (
    ExternalRepositoryOrigin,
    ManagedGrpcPythonEnvRepositoryLocationOrigin,
)
from dagster.core.scheduler.job import (
    JobState,
    JobStatus,
    JobTickData,
    JobTickStatus,
    JobType,
    ScheduleJobData,
)
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.seven import get_current_datetime_in_utc
from dagster.utils.error import SerializableErrorInfo

FAKE_SCHEDULER_NAME = "FakeSchedulerClassName"

OTHER_FAKE_SCHEDULER_NAME = "OtherFakeSchedulerClassName"


class TestScheduleStorage:
    """
    You can extend this class to easily run these set of tests on any schedule storage. When extending,
    you simply need to override the `schedule_storage` fixture and return your implementation of
    `ScheduleStorage`.

    For example:

    ```
    class TestMyStorageImplementation(TestScheduleStorage):
        __test__ = True

        @pytest.fixture(scope='function', name='storage')
        def schedule_storage(self):  # pylint: disable=arguments-differ
            return MyStorageImplementation()
    ```
    """

    __test__ = False

    @pytest.fixture(name="storage", params=[])
    def schedule_storage(self, request):
        with request.param() as s:
            yield s

    @staticmethod
    def fake_repo_target():
        return ExternalRepositoryOrigin(
            ManagedGrpcPythonEnvRepositoryLocationOrigin(
                LoadableTargetOrigin(
                    executable_path=sys.executable, module_name="fake", attribute="fake"
                ),
            ),
            "fake_repo_name",
        )

    @classmethod
    def build_schedule(
        cls, schedule_name, cron_schedule, status=JobStatus.STOPPED, scheduler=FAKE_SCHEDULER_NAME
    ):
        return JobState(
            cls.fake_repo_target().get_job_origin(schedule_name),
            JobType.SCHEDULE,
            status,
            ScheduleJobData(cron_schedule, start_timestamp=None, scheduler=scheduler),
        )

    @classmethod
    def build_sensor(cls, sensor_name, status=JobStatus.STOPPED):
        external_job_origin = cls.fake_repo_target().get_job_origin(sensor_name)
        return JobState(external_job_origin, JobType.SENSOR, status)

    def test_basic_schedule_storage(self, storage):
        assert storage

        schedule = self.build_schedule("my_schedule", "* * * * *")
        storage.add_job_state(schedule)
        schedules = storage.all_stored_job_state(
            self.fake_repo_target().get_id(),
            JobType.SCHEDULE,
        )
        assert len(schedules) == 1

        schedule = schedules[0]
        assert schedule.job_name == "my_schedule"
        assert schedule.job_specific_data.cron_schedule == "* * * * *"
        assert schedule.job_specific_data.start_timestamp == None
        assert schedule.job_specific_data.scheduler == FAKE_SCHEDULER_NAME

    def test_add_multiple_schedules(self, storage):
        assert storage

        schedule = self.build_schedule("my_schedule", "* * * * *")
        schedule_2 = self.build_schedule("my_schedule_2", "* * * * *")
        schedule_3 = self.build_schedule("my_schedule_3", "* * * * *")

        storage.add_job_state(schedule)
        storage.add_job_state(schedule_2)
        storage.add_job_state(schedule_3)

        schedules = storage.all_stored_job_state(self.fake_repo_target().get_id(), JobType.SCHEDULE)
        assert len(schedules) == 3

        assert any(s.job_name == "my_schedule" for s in schedules)
        assert any(s.job_name == "my_schedule_2" for s in schedules)
        assert any(s.job_name == "my_schedule_3" for s in schedules)

        assert all(s.job_specific_data.scheduler == FAKE_SCHEDULER_NAME for s in schedules)

    def test_get_schedule_state(self, storage):
        assert storage

        state = self.build_schedule("my_schedule", "* * * * *")
        storage.add_job_state(state)
        schedule = storage.get_job_state(state.job_origin_id)

        assert schedule.job_name == "my_schedule"
        assert schedule.job_specific_data.start_timestamp == None
        assert schedule.job_specific_data.scheduler == FAKE_SCHEDULER_NAME

    def test_get_schedule_state_not_found(self, storage):
        assert storage

        storage.add_job_state(self.build_schedule("my_schedule", "* * * * *"))
        schedule = storage.get_job_state("fake_id")

        assert schedule is None

    def test_update_schedule(self, storage):
        assert storage

        schedule = self.build_schedule("my_schedule", "* * * * *")
        storage.add_job_state(schedule)

        now_time = get_current_datetime_in_utc().timestamp()

        new_schedule = schedule.with_status(JobStatus.RUNNING).with_data(
            ScheduleJobData(
                cron_schedule=schedule.job_specific_data.cron_schedule,
                start_timestamp=now_time,
                scheduler=FAKE_SCHEDULER_NAME,
            )
        )
        storage.update_job_state(new_schedule)

        schedules = storage.all_stored_job_state(self.fake_repo_target().get_id(), JobType.SCHEDULE)
        assert len(schedules) == 1

        schedule = schedules[0]
        assert schedule.job_name == "my_schedule"
        assert schedule.status == JobStatus.RUNNING
        assert schedule.job_specific_data.start_timestamp == now_time
        assert schedule.job_specific_data.scheduler == FAKE_SCHEDULER_NAME

        stopped_schedule = schedule.with_status(JobStatus.STOPPED).with_data(
            ScheduleJobData(schedule.job_specific_data.cron_schedule, scheduler=FAKE_SCHEDULER_NAME)
        )
        storage.update_job_state(stopped_schedule)

        schedules = storage.all_stored_job_state(self.fake_repo_target().get_id(), JobType.SCHEDULE)
        assert len(schedules) == 1

        schedule = schedules[0]
        assert schedule.job_name == "my_schedule"
        assert schedule.status == JobStatus.STOPPED
        assert schedule.job_specific_data.start_timestamp == None
        assert schedule.job_specific_data.scheduler == FAKE_SCHEDULER_NAME

    def test_update_schedule_not_found(self, storage):
        assert storage

        schedule = self.build_schedule("my_schedule", "* * * * *")

        with pytest.raises(DagsterInvariantViolationError):
            storage.update_job_state(schedule)

    def test_delete_schedule_state(self, storage):
        assert storage

        schedule = self.build_schedule("my_schedule", "* * * * *")
        storage.add_job_state(schedule)
        storage.delete_job_state(schedule.job_origin_id)

        schedules = storage.all_stored_job_state(self.fake_repo_target().get_id(), JobType.SCHEDULE)
        assert len(schedules) == 0

    def test_delete_schedule_not_found(self, storage):
        assert storage

        schedule = self.build_schedule("my_schedule", "* * * * *")

        with pytest.raises(DagsterInvariantViolationError):
            storage.delete_job_state(schedule.job_origin_id)

    def test_add_schedule_with_same_name(self, storage):
        assert storage

        schedule = self.build_schedule("my_schedule", "* * * * *")
        storage.add_job_state(schedule)

        with pytest.raises(DagsterInvariantViolationError):
            storage.add_job_state(schedule)

    def build_tick(self, current_time, status=JobTickStatus.STARTED, run_id=None, error=None):
        return JobTickData(
            "my_schedule",
            "my_schedule",
            JobType.SCHEDULE,
            status,
            current_time,
            [run_id] if run_id else [],
            [],
            error,
        )

    def test_create_tick(self, storage):
        assert storage

        current_time = time.time()
        tick = storage.create_job_tick(self.build_tick(current_time))
        ticks = storage.get_job_ticks("my_schedule")
        assert len(ticks) == 1
        tick = ticks[0]
        assert tick.job_name == "my_schedule"
        assert tick.timestamp == current_time
        assert tick.status == JobTickStatus.STARTED
        assert tick.run_ids == []
        assert tick.error == None

    def test_update_tick_to_success(self, storage):
        assert storage

        current_time = time.time()
        tick = storage.create_job_tick(self.build_tick(current_time))

        updated_tick = tick.with_status(JobTickStatus.SUCCESS).with_run(run_id="1234")
        assert updated_tick.status == JobTickStatus.SUCCESS

        storage.update_job_tick(updated_tick)

        ticks = storage.get_job_ticks("my_schedule")
        assert len(ticks) == 1
        tick = ticks[0]
        assert tick.job_name == "my_schedule"
        assert tick.timestamp == current_time
        assert tick.status == JobTickStatus.SUCCESS
        assert tick.run_ids == ["1234"]
        assert tick.error == None

    def test_update_tick_to_skip(self, storage):
        assert storage

        current_time = time.time()
        tick = storage.create_job_tick(self.build_tick(current_time))

        updated_tick = tick.with_status(JobTickStatus.SKIPPED)
        assert updated_tick.status == JobTickStatus.SKIPPED

        storage.update_job_tick(updated_tick)

        ticks = storage.get_job_ticks("my_schedule")
        assert len(ticks) == 1
        tick = ticks[0]
        assert tick.job_name == "my_schedule"
        assert tick.timestamp == current_time
        assert tick.status == JobTickStatus.SKIPPED
        assert tick.run_ids == []
        assert tick.error == None

    def test_update_tick_to_failure(self, storage):
        assert storage

        current_time = time.time()
        tick = storage.create_job_tick(self.build_tick(current_time))

        updated_tick = tick.with_status(
            JobTickStatus.FAILURE,
            error=SerializableErrorInfo(message="Error", stack=[], cls_name="TestError"),
        )
        assert updated_tick.status == JobTickStatus.FAILURE

        storage.update_job_tick(updated_tick)

        ticks = storage.get_job_ticks("my_schedule")
        assert len(ticks) == 1
        tick = ticks[0]
        assert tick.tick_id == 1
        assert tick.job_name == "my_schedule"
        assert tick.timestamp == current_time
        assert tick.status == JobTickStatus.FAILURE
        assert tick.run_ids == []
        assert tick.error == SerializableErrorInfo(message="Error", stack=[], cls_name="TestError")

    def test_get_tick_stats(self, storage):
        assert storage

        current_time = time.time()

        error = SerializableErrorInfo(message="Error", stack=[], cls_name="TestError")

        # Create ticks
        for x in range(2):
            storage.create_job_tick(self.build_tick(current_time))

        for x in range(3):
            storage.create_job_tick(
                self.build_tick(current_time, JobTickStatus.SUCCESS, run_id=str(x)),
            )

        for x in range(4):
            storage.create_job_tick(
                self.build_tick(current_time, JobTickStatus.SKIPPED),
            )

        for x in range(5):
            storage.create_job_tick(
                self.build_tick(current_time, JobTickStatus.FAILURE, error=error),
            )

        stats = storage.get_job_tick_stats("my_schedule")
        assert stats.ticks_started == 2
        assert stats.ticks_succeeded == 3
        assert stats.ticks_skipped == 4
        assert stats.ticks_failed == 5

    def test_basic_job_storage(self, storage):
        assert storage
        job = self.build_sensor("my_sensor")
        storage.add_job_state(job)
        jobs = storage.all_stored_job_state(self.fake_repo_target().get_id())
        assert len(jobs) == 1

        job = jobs[0]
        assert job.job_name == "my_sensor"

    def test_add_multiple_jobs(self, storage):
        assert storage

        job = self.build_sensor("my_sensor")
        job_2 = self.build_sensor("my_sensor_2")
        job_3 = self.build_sensor("my_sensor_3")

        storage.add_job_state(job)
        storage.add_job_state(job_2)
        storage.add_job_state(job_3)

        jobs = storage.all_stored_job_state(self.fake_repo_target().get_id())
        assert len(jobs) == 3

        assert any(s.job_name == "my_sensor" for s in jobs)
        assert any(s.job_name == "my_sensor_2" for s in jobs)
        assert any(s.job_name == "my_sensor_3" for s in jobs)

    def test_get_job_state(self, storage):
        assert storage

        state = self.build_sensor("my_sensor")
        storage.add_job_state(state)
        job = storage.get_job_state(state.job_origin_id)

        assert job.job_name == "my_sensor"

    def test_get_job_state_not_found(self, storage):
        assert storage

        storage.add_job_state(self.build_sensor("my_sensor"))
        job_state = storage.get_job_state("fake_id")
        assert job_state is None

    def test_update_job(self, storage):
        assert storage

        job = self.build_sensor("my_sensor")
        storage.add_job_state(job)

        new_job = job.with_status(JobStatus.RUNNING)
        storage.update_job_state(new_job)

        jobs = storage.all_stored_job_state(self.fake_repo_target().get_id())
        assert len(jobs) == 1

        job = jobs[0]
        assert job.job_name == "my_sensor"
        assert job.status == JobStatus.RUNNING

        stopped_job = job.with_status(JobStatus.STOPPED)
        storage.update_job_state(stopped_job)

        jobs = storage.all_stored_job_state(self.fake_repo_target().get_id())
        assert len(jobs) == 1

        job = jobs[0]
        assert job.job_name == "my_sensor"
        assert job.status == JobStatus.STOPPED

    def test_update_job_not_found(self, storage):
        assert storage

        job = self.build_sensor("my_sensor")

        with pytest.raises(DagsterInvariantViolationError):
            storage.update_job_state(job)

    def test_delete_job_state(self, storage):
        assert storage
        job = self.build_sensor("my_sensor")
        storage.add_job_state(job)
        storage.delete_job_state(job.job_origin_id)

        jobs = storage.all_stored_job_state(self.fake_repo_target().get_id())
        assert len(jobs) == 0

    def test_delete_job_not_found(self, storage):
        assert storage

        job = self.build_sensor("my_sensor")

        with pytest.raises(DagsterInvariantViolationError):
            storage.delete_job_state(job.job_origin_id)

    def test_add_job_with_same_name(self, storage):
        assert storage

        job = self.build_sensor("my_sensor")
        storage.add_job_state(job)

        with pytest.raises(DagsterInvariantViolationError):
            storage.add_job_state(job)

    def build_sensor_tick(
        self, current_time, status=JobTickStatus.STARTED, run_id=None, error=None
    ):
        return JobTickData(
            "my_sensor",
            "my_sensor",
            JobType.SENSOR,
            status,
            current_time,
            [run_id] if run_id else [],
            error,
        )

    def test_create_job_tick(self, storage):
        assert storage

        current_time = time.time()
        tick = storage.create_job_tick(self.build_sensor_tick(current_time))
        assert tick.tick_id == 1

        ticks = storage.get_job_ticks("my_sensor")
        assert len(ticks) == 1
        tick = ticks[0]
        assert tick.tick_id == 1
        assert tick.job_name == "my_sensor"
        assert tick.timestamp == current_time
        assert tick.status == JobTickStatus.STARTED
        assert tick.run_ids == []
        assert tick.error == None

    def test_get_job_tick(self, storage):
        assert storage
        now = pendulum.now()
        five_days_ago = now.subtract(days=5).timestamp()
        four_days_ago = now.subtract(days=4).timestamp()
        one_day_ago = now.subtract(days=1).timestamp()

        storage.create_job_tick(self.build_sensor_tick(five_days_ago, JobTickStatus.SKIPPED))
        storage.create_job_tick(self.build_sensor_tick(four_days_ago, JobTickStatus.SKIPPED))
        storage.create_job_tick(self.build_sensor_tick(one_day_ago, JobTickStatus.SKIPPED))
        ticks = storage.get_job_ticks("my_sensor")
        assert len(ticks) == 3

        ticks = storage.get_job_ticks("my_sensor", after=five_days_ago + 1)
        assert len(ticks) == 2
        ticks = storage.get_job_ticks("my_sensor", before=one_day_ago - 1)
        assert len(ticks) == 2
        ticks = storage.get_job_ticks("my_sensor", after=five_days_ago + 1, before=one_day_ago - 1)
        assert len(ticks) == 1

    def test_update_job_tick_to_success(self, storage):
        assert storage

        current_time = time.time()
        tick = storage.create_job_tick(self.build_sensor_tick(current_time))

        updated_tick = tick.with_status(JobTickStatus.SUCCESS).with_run(run_id="1234")
        assert updated_tick.status == JobTickStatus.SUCCESS

        storage.update_job_tick(updated_tick)

        ticks = storage.get_job_ticks("my_sensor")
        assert len(ticks) == 1
        tick = ticks[0]
        assert tick.tick_id == 1
        assert tick.job_name == "my_sensor"
        assert tick.timestamp == current_time
        assert tick.status == JobTickStatus.SUCCESS
        assert tick.run_ids == ["1234"]
        assert tick.error == None

    def test_update_job_tick_to_skip(self, storage):
        assert storage

        current_time = time.time()
        tick = storage.create_job_tick(self.build_sensor_tick(current_time))

        updated_tick = tick.with_status(JobTickStatus.SKIPPED)
        assert updated_tick.status == JobTickStatus.SKIPPED

        storage.update_job_tick(updated_tick)

        ticks = storage.get_job_ticks("my_sensor")
        assert len(ticks) == 1
        tick = ticks[0]
        assert tick.tick_id == 1
        assert tick.job_name == "my_sensor"
        assert tick.timestamp == current_time
        assert tick.status == JobTickStatus.SKIPPED
        assert tick.run_ids == []
        assert tick.error == None

    def test_update_job_tick_to_failure(self, storage):
        assert storage

        current_time = time.time()
        tick = storage.create_job_tick(self.build_sensor_tick(current_time))
        error = SerializableErrorInfo(message="Error", stack=[], cls_name="TestError")

        updated_tick = tick.with_status(JobTickStatus.FAILURE, error=error)
        assert updated_tick.status == JobTickStatus.FAILURE

        storage.update_job_tick(updated_tick)

        ticks = storage.get_job_ticks("my_sensor")
        assert len(ticks) == 1
        tick = ticks[0]
        assert tick.tick_id == 1
        assert tick.job_name == "my_sensor"
        assert tick.timestamp == current_time
        assert tick.status == JobTickStatus.FAILURE
        assert tick.run_ids == []
        assert tick.error == error

    def test_purge_job_ticks(self, storage):
        assert storage

        now = pendulum.now()
        five_minutes_ago = now.subtract(minutes=5).timestamp()
        four_minutes_ago = now.subtract(minutes=4).timestamp()
        one_minute_ago = now.subtract(minutes=1).timestamp()
        storage.create_job_tick(self.build_sensor_tick(five_minutes_ago, JobTickStatus.SKIPPED))
        storage.create_job_tick(
            self.build_sensor_tick(four_minutes_ago, JobTickStatus.SUCCESS, run_id="fake_run_id")
        )
        storage.create_job_tick(self.build_sensor_tick(one_minute_ago, JobTickStatus.SKIPPED))
        ticks = storage.get_job_ticks("my_sensor")
        assert len(ticks) == 3

        storage.purge_job_ticks("my_sensor", JobTickStatus.SKIPPED, now.subtract(minutes=2))

        ticks = storage.get_job_ticks("my_sensor")
        assert len(ticks) == 2

    def test_migrate_schedulers(self, storage):
        schedule = self.build_schedule("my_schedule", "* * * * *")
        storage.add_job_state(schedule)

        # changing if its not running is fine
        storage.validate_stored_schedules(OTHER_FAKE_SCHEDULER_NAME)

        running_schedule = self.build_schedule(
            "my_other_schedule", "* * * * *", status=JobStatus.RUNNING
        )
        storage.add_job_state(running_schedule)

        with pytest.raises(
            DagsterScheduleWipeRequired,
            match=re.escape(
                "Found a running schedule using a scheduler (FakeSchedulerClassName) "
                "that differs from the scheduler on the instance (OtherFakeSchedulerClassName). "
                "The most likely reason for this error is that you changed the scheduler on your "
                "instance while it was still running schedules. To fix this, change the scheduler "
                "on your instance back to the previous scheduler configuration and run the command "
                "'dagster schedule wipe'. It will then be safe to change back "
                "to OtherFakeSchedulerClassName."
            ),
        ):
            storage.validate_stored_schedules(OTHER_FAKE_SCHEDULER_NAME)

        storage.wipe()

        # Now passes
        storage.validate_stored_schedules(OTHER_FAKE_SCHEDULER_NAME)
