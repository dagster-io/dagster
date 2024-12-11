import sys
import time

import pytest

from dagster import StaticPartitionsDefinition
from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset
from dagster._core.definitions.asset_key import AssetCheckKey
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AssetSubsetWithMetadata,
    AutomationConditionEvaluation,
    AutomationConditionNodeSnapshot,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.remote_representation import (
    ManagedGrpcPythonEnvCodeLocationOrigin,
    RemoteRepositoryOrigin,
)
from dagster._core.scheduler.instigation import (
    InstigatorState,
    InstigatorStatus,
    InstigatorType,
    ScheduleInstigatorData,
    TickData,
    TickStatus,
)
from dagster._core.test_utils import freeze_time
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._time import get_current_datetime
from dagster._utils.error import SerializableErrorInfo
from dagster._vendored.dateutil.relativedelta import relativedelta


class TestScheduleStorage:
    """You can extend this class to easily run these set of tests on any schedule storage. When extending,
    you simply need to override the `schedule_storage` fixture and return your implementation of
    `ScheduleStorage`.

    For example:

    ```
    class TestMyStorageImplementation(TestScheduleStorage):
        __test__ = True

        @pytest.fixture(scope='function', name='storage')
        def schedule_storage(self):
            return MyStorageImplementation()
    ```
    """

    __test__ = False

    @pytest.fixture(name="storage", params=[])
    def schedule_storage(self, request):
        with request.param() as s:
            yield s

    # Override this for schedule storages that are not allowed to delete state or ticks
    def can_delete(self):
        return True

    def can_purge(self):
        return True

    def can_store_auto_materialize_asset_evaluations(self):
        return True

    def can_get_single_tick(self):
        return True

    @staticmethod
    def fake_repo_target():
        return RemoteRepositoryOrigin(
            ManagedGrpcPythonEnvCodeLocationOrigin(
                LoadableTargetOrigin(
                    executable_path=sys.executable, module_name="fake", attribute="fake"
                ),
            ),
            "fake_repo_name",
        )

    @classmethod
    def build_schedule(
        cls,
        schedule_name,
        cron_schedule,
        status=InstigatorStatus.STOPPED,
    ):
        return InstigatorState(
            cls.fake_repo_target().get_instigator_origin(schedule_name),
            InstigatorType.SCHEDULE,
            status,
            ScheduleInstigatorData(cron_schedule, start_timestamp=None),
        )

    @classmethod
    def build_sensor(cls, sensor_name, status=InstigatorStatus.STOPPED):
        origin = cls.fake_repo_target().get_instigator_origin(sensor_name)
        return InstigatorState(origin, InstigatorType.SENSOR, status)

    def test_basic_schedule_storage(self, storage):
        assert storage

        schedule = self.build_schedule("my_schedule", "* * * * *")
        storage.add_instigator_state(schedule)
        schedules = storage.all_instigator_state(
            self.fake_repo_target().get_id(),
            self.fake_repo_target().get_selector_id(),
            InstigatorType.SCHEDULE,
        )
        assert len(schedules) == 1

        schedule = schedules[0]
        assert schedule.instigator_name == "my_schedule"
        assert schedule.instigator_data.cron_schedule == "* * * * *"
        assert schedule.instigator_data.start_timestamp is None

    def test_instigator_status_backcompat(self, storage):
        assert storage

        schedule = self.build_schedule(
            "my_instigator_status_backcompat",
            "* * * * *",
            status=InstigatorStatus.AUTOMATICALLY_RUNNING,
        )
        storage.add_instigator_state(schedule)
        schedules = storage.all_instigator_state(
            self.fake_repo_target().get_id(),
            self.fake_repo_target().get_selector_id(),
            InstigatorType.SCHEDULE,
        )
        assert len(schedules) == 1

        schedule = schedules[0]
        assert schedule.instigator_name == "my_instigator_status_backcompat"
        assert schedule.instigator_data.cron_schedule == "* * * * *"
        assert schedule.instigator_data.start_timestamp is None
        assert schedule.status == InstigatorStatus.DECLARED_IN_CODE

    def test_add_multiple_schedules(self, storage):
        assert storage

        schedule = self.build_schedule("my_schedule", "* * * * *", status=InstigatorStatus.RUNNING)
        schedule_2 = self.build_schedule(
            "my_schedule_2", "* * * * *", status=InstigatorStatus.STOPPED
        )
        schedule_3 = self.build_schedule(
            "my_schedule_3", "* * * * *", status=InstigatorStatus.DECLARED_IN_CODE
        )

        storage.add_instigator_state(schedule)
        storage.add_instigator_state(schedule_2)
        storage.add_instigator_state(schedule_3)

        schedules = storage.all_instigator_state(
            self.fake_repo_target().get_id(),
            self.fake_repo_target().get_selector_id(),
            InstigatorType.SCHEDULE,
        )
        assert len(schedules) == 3

        assert any(s.instigator_name == "my_schedule" for s in schedules)
        assert any(s.instigator_name == "my_schedule_2" for s in schedules)
        assert any(s.instigator_name == "my_schedule_3" for s in schedules)

        running = storage.all_instigator_state(
            self.fake_repo_target().get_id(),
            self.fake_repo_target().get_selector_id(),
            InstigatorType.SCHEDULE,
            {InstigatorStatus.RUNNING, InstigatorStatus.DECLARED_IN_CODE},
        )
        assert len(running) == 2
        assert "my_schedule" in [state.instigator_name for state in running]
        assert "my_schedule_3" in [state.instigator_name for state in running]

        stopped = storage.all_instigator_state(
            self.fake_repo_target().get_id(),
            self.fake_repo_target().get_selector_id(),
            InstigatorType.SCHEDULE,
            {InstigatorStatus.STOPPED},
        )
        assert len(stopped) == 1
        assert stopped[0].instigator_name == "my_schedule_2"

    def test_get_schedule_state(self, storage):
        assert storage

        state = self.build_schedule("my_schedule", "* * * * *")
        storage.add_instigator_state(state)
        schedule = storage.get_instigator_state(state.instigator_origin_id, state.selector_id)

        assert schedule.instigator_name == "my_schedule"
        assert schedule.instigator_data.start_timestamp is None

    def test_get_schedule_state_not_found(self, storage):
        assert storage

        state = self.build_schedule("my_schedule", "* * * * *")
        storage.add_instigator_state(state)
        schedule = storage.get_instigator_state("fake_id", "fake_selector")

        assert schedule is None

    def test_update_schedule(self, storage):
        assert storage

        schedule = self.build_schedule("my_schedule", "* * * * *")
        storage.add_instigator_state(schedule)

        now_time = time.time()

        new_schedule = schedule.with_status(InstigatorStatus.RUNNING).with_data(
            ScheduleInstigatorData(
                cron_schedule=schedule.instigator_data.cron_schedule,  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
                start_timestamp=now_time,
            )
        )
        storage.update_instigator_state(new_schedule)

        schedules = storage.all_instigator_state(
            self.fake_repo_target().get_id(),
            self.fake_repo_target().get_selector_id(),
            InstigatorType.SCHEDULE,
        )
        assert len(schedules) == 1

        schedule = schedules[0]
        assert schedule.instigator_name == "my_schedule"
        assert schedule.status == InstigatorStatus.RUNNING
        assert schedule.instigator_data.start_timestamp == now_time

        stopped_schedule = schedule.with_status(InstigatorStatus.STOPPED).with_data(
            ScheduleInstigatorData(schedule.instigator_data.cron_schedule)
        )
        storage.update_instigator_state(stopped_schedule)

        schedules = storage.all_instigator_state(
            self.fake_repo_target().get_id(),
            self.fake_repo_target().get_selector_id(),
            InstigatorType.SCHEDULE,
        )
        assert len(schedules) == 1

        schedule = schedules[0]
        assert schedule.instigator_name == "my_schedule"
        assert schedule.status == InstigatorStatus.STOPPED
        assert schedule.instigator_data.start_timestamp is None

    def test_update_schedule_not_found(self, storage):
        assert storage

        schedule = self.build_schedule("my_schedule", "* * * * *")

        with pytest.raises(Exception):
            storage.update_instigator_state(schedule)

    def test_delete_schedule_state(self, storage):
        assert storage

        if not self.can_delete():
            pytest.skip("Storage cannot delete")

        schedule = self.build_schedule("my_schedule", "* * * * *")
        storage.add_instigator_state(schedule)
        storage.delete_instigator_state(schedule.instigator_origin_id, schedule.selector_id)

        schedules = storage.all_instigator_state(
            self.fake_repo_target().get_id(),
            self.fake_repo_target().get_selector_id(),
            InstigatorType.SCHEDULE,
        )
        assert len(schedules) == 0

    def test_delete_schedule_not_found(self, storage):
        assert storage

        if not self.can_delete():
            pytest.skip("Storage cannot delete")

        schedule = self.build_schedule("my_schedule", "* * * * *")

        with pytest.raises(Exception):
            storage.delete_instigator_state(schedule.instigator_origin_id, schedule.selector_id)

    def test_add_schedule_with_same_name(self, storage):
        assert storage

        schedule = self.build_schedule("my_schedule", "* * * * *")
        storage.add_instigator_state(schedule)

        with pytest.raises(Exception):
            storage.add_instigator_state(schedule)

    def build_schedule_tick(self, current_time, status=TickStatus.STARTED, run_id=None, error=None):
        return TickData(
            "my_schedule",
            "my_schedule",
            InstigatorType.SCHEDULE,
            status,
            current_time,
            [run_id] if run_id else [],
            [],
            error,
            selector_id="my_schedule",
        )

    def test_create_tick(self, storage):
        assert storage

        current_time = time.time()
        tick = storage.create_tick(self.build_schedule_tick(current_time))
        ticks = storage.get_ticks("my_schedule", "my_schedule")
        assert len(ticks) == 1
        tick = ticks[0]
        assert tick.instigator_name == "my_schedule"
        assert tick.timestamp == current_time
        assert tick.status == TickStatus.STARTED
        assert tick.run_ids == []
        assert tick.error is None

    def test_update_tick_to_success(self, storage):
        assert storage

        current_time = time.time()
        tick = storage.create_tick(self.build_schedule_tick(current_time))

        assert not tick.end_timestamp

        freeze_datetime = get_current_datetime()

        with freeze_time(freeze_datetime):
            updated_tick = tick.with_status(TickStatus.SUCCESS).with_run_info(run_id="1234")
            assert updated_tick.status == TickStatus.SUCCESS
            assert updated_tick.end_timestamp == freeze_datetime.timestamp()

        storage.update_tick(updated_tick)

        ticks = storage.get_ticks("my_schedule", "my_schedule")
        assert len(ticks) == 1
        tick = ticks[0]
        assert tick.instigator_name == "my_schedule"
        assert tick.timestamp == current_time
        assert tick.status == TickStatus.SUCCESS
        assert tick.run_ids == ["1234"]
        assert tick.error is None

    def test_update_tick_to_skip(self, storage):
        assert storage

        current_time = time.time()
        tick = storage.create_tick(self.build_schedule_tick(current_time))
        assert not tick.end_timestamp

        freeze_datetime = get_current_datetime()

        with freeze_time(freeze_datetime):
            updated_tick = tick.with_status(TickStatus.SKIPPED)
            assert updated_tick.status == TickStatus.SKIPPED
            assert updated_tick.end_timestamp == freeze_datetime.timestamp()

        storage.update_tick(updated_tick)

        ticks = storage.get_ticks("my_schedule", "my_schedule")
        assert len(ticks) == 1
        tick = ticks[0]
        assert tick.instigator_name == "my_schedule"
        assert tick.timestamp == current_time
        assert tick.status == TickStatus.SKIPPED
        assert tick.run_ids == []
        assert tick.error is None

    def test_update_tick_to_failure(self, storage):
        assert storage

        current_time = time.time()
        tick = storage.create_tick(self.build_schedule_tick(current_time))

        freeze_datetime = get_current_datetime()

        with freeze_time(freeze_datetime):
            updated_tick = tick.with_status(
                TickStatus.FAILURE,
                error=SerializableErrorInfo(message="Error", stack=[], cls_name="TestError"),
            )
            assert updated_tick.status == TickStatus.FAILURE
            assert updated_tick.end_timestamp == freeze_datetime.timestamp()

        storage.update_tick(updated_tick)

        ticks = storage.get_ticks("my_schedule", "my_schedule")
        assert len(ticks) == 1
        tick = ticks[0]
        assert tick.tick_id > 0
        assert tick.instigator_name == "my_schedule"
        assert tick.timestamp == current_time
        assert tick.status == TickStatus.FAILURE
        assert tick.run_ids == []
        assert tick.error == SerializableErrorInfo(message="Error", stack=[], cls_name="TestError")

    def test_basic_storage(self, storage):
        assert storage
        sensor_state = self.build_sensor("my_sensor")
        storage.add_instigator_state(sensor_state)
        states = storage.all_instigator_state(
            self.fake_repo_target().get_id(), self.fake_repo_target().get_selector_id()
        )
        assert len(states) == 1

        state = states[0]
        assert state.instigator_name == "my_sensor"

    def test_add_multiple_states(self, storage):
        assert storage

        state = self.build_sensor("my_sensor")
        state_2 = self.build_sensor("my_sensor_2")
        state_3 = self.build_sensor("my_sensor_3")

        storage.add_instigator_state(state)
        storage.add_instigator_state(state_2)
        storage.add_instigator_state(state_3)

        states = storage.all_instigator_state(
            self.fake_repo_target().get_id(), self.fake_repo_target().get_selector_id()
        )
        assert len(states) == 3

        assert any(s.instigator_name == "my_sensor" for s in states)
        assert any(s.instigator_name == "my_sensor_2" for s in states)
        assert any(s.instigator_name == "my_sensor_3" for s in states)

    def test_get_instigator_state(self, storage):
        assert storage

        state = self.build_sensor("my_sensor")
        storage.add_instigator_state(state)
        state = storage.get_instigator_state(state.instigator_origin_id, state.selector_id)

        assert state.instigator_name == "my_sensor"

    def test_get_instigator_state_not_found(self, storage):
        assert storage

        storage.add_instigator_state(self.build_sensor("my_sensor"))
        state = storage.get_instigator_state("fake_id", "fake_selector")
        assert state is None

    def test_update_state(self, storage):
        assert storage

        state = self.build_sensor("my_sensor")
        storage.add_instigator_state(state)

        new_state = state.with_status(InstigatorStatus.RUNNING)
        storage.update_instigator_state(new_state)

        states = storage.all_instigator_state(
            self.fake_repo_target().get_id(), self.fake_repo_target().get_selector_id()
        )
        assert len(states) == 1

        state = states[0]
        assert state.instigator_name == "my_sensor"
        assert state.status == InstigatorStatus.RUNNING

        stopped_state = state.with_status(InstigatorStatus.STOPPED)
        storage.update_instigator_state(stopped_state)

        states = storage.all_instigator_state(
            self.fake_repo_target().get_id(), self.fake_repo_target().get_selector_id()
        )
        assert len(states) == 1

        state = states[0]
        assert state.instigator_name == "my_sensor"
        assert state.status == InstigatorStatus.STOPPED

    def test_update_state_not_found(self, storage):
        assert storage

        state = self.build_sensor("my_sensor")

        with pytest.raises(Exception):
            storage.update_instigator_state(state)

    def test_delete_instigator_state(self, storage):
        assert storage

        if not self.can_delete():
            pytest.skip("Storage cannot delete")

        state = self.build_sensor("my_sensor")
        storage.add_instigator_state(state)
        storage.delete_instigator_state(state.instigator_origin_id, state.selector_id)

        states = storage.all_instigator_state(
            self.fake_repo_target().get_id(), self.fake_repo_target().get_selector_id()
        )
        assert len(states) == 0

    def test_delete_state_not_found(self, storage):
        assert storage

        if not self.can_delete():
            pytest.skip("Storage cannot delete")

        state = self.build_sensor("my_sensor")

        with pytest.raises(Exception):
            storage.delete_instigator_state(state.instigator_origin_id, state.selector_id)

    def test_add_state_with_same_name(self, storage):
        assert storage

        state = self.build_sensor("my_sensor")
        storage.add_instigator_state(state)

        with pytest.raises(Exception):
            storage.add_instigator_state(state)

    def build_sensor_tick(
        self, current_time, status=TickStatus.STARTED, run_id=None, error=None, name="my_sensor"
    ):
        return TickData(
            name,
            name,
            InstigatorType.SENSOR,
            status,
            current_time,
            [run_id] if run_id else [],
            error=error,
            selector_id=name,
        )

    def test_create_sensor_tick(self, storage):
        assert storage

        current_time = time.time()
        tick = storage.create_tick(self.build_sensor_tick(current_time))
        tick_id = tick.tick_id

        ticks = storage.get_ticks("my_sensor", "my_sensor")
        assert len(ticks) == 1
        tick = ticks[0]
        assert tick.tick_id == tick_id
        assert tick.instigator_name == "my_sensor"
        assert tick.timestamp == current_time
        assert tick.status == TickStatus.STARTED
        assert tick.run_ids == []
        assert tick.error is None

    def test_get_sensor_tick(self, storage):
        assert storage
        now = get_current_datetime()
        five_days_ago = (now - relativedelta(days=5)).timestamp()
        four_days_ago = (now - relativedelta(days=4)).timestamp()
        one_day_ago = (now - relativedelta(days=1)).timestamp()

        five_days_ago_tick = storage.create_tick(
            self.build_sensor_tick(five_days_ago, TickStatus.SKIPPED)
        )
        storage.create_tick(self.build_sensor_tick(four_days_ago, TickStatus.SKIPPED))
        storage.create_tick(self.build_sensor_tick(one_day_ago, TickStatus.SKIPPED))
        ticks = storage.get_ticks("my_sensor", "my_sensor")
        assert len(ticks) == 3

        ticks = storage.get_ticks("my_sensor", "my_sensor", after=five_days_ago + 1)
        assert len(ticks) == 2
        ticks = storage.get_ticks("my_sensor", "my_sensor", before=one_day_ago - 1)
        assert len(ticks) == 2
        ticks = storage.get_ticks(
            "my_sensor", "my_sensor", after=five_days_ago + 1, before=one_day_ago - 1
        )
        assert len(ticks) == 1

        if self.can_get_single_tick():
            assert storage.get_tick(five_days_ago_tick.tick_id)

    def test_update_sensor_tick_to_success(self, storage):
        assert storage

        current_time = time.time()
        tick = storage.create_tick(self.build_sensor_tick(current_time))

        updated_tick = tick.with_status(TickStatus.SUCCESS).with_run_info(run_id="1234")
        assert updated_tick.status == TickStatus.SUCCESS

        storage.update_tick(updated_tick)

        ticks = storage.get_ticks("my_sensor", "my_sensor")
        assert len(ticks) == 1
        tick = ticks[0]
        assert tick.tick_id > 0
        assert tick.instigator_name == "my_sensor"
        assert tick.timestamp == current_time
        assert tick.status == TickStatus.SUCCESS
        assert tick.run_ids == ["1234"]
        assert tick.error is None

    def test_update_sensor_tick_to_skip(self, storage):
        assert storage

        current_time = time.time()
        tick = storage.create_tick(self.build_sensor_tick(current_time))

        updated_tick = tick.with_status(TickStatus.SKIPPED)
        assert updated_tick.status == TickStatus.SKIPPED

        storage.update_tick(updated_tick)

        ticks = storage.get_ticks("my_sensor", "my_sensor")
        assert len(ticks) == 1
        tick = ticks[0]
        assert tick.tick_id > 0
        assert tick.instigator_name == "my_sensor"
        assert tick.timestamp == current_time
        assert tick.status == TickStatus.SKIPPED
        assert tick.run_ids == []
        assert tick.error is None

    def test_update_sensor_tick_to_failure(self, storage):
        assert storage

        current_time = time.time()
        tick = storage.create_tick(self.build_sensor_tick(current_time))
        error = SerializableErrorInfo(message="Error", stack=[], cls_name="TestError")

        updated_tick = tick.with_status(TickStatus.FAILURE, error=error)
        assert updated_tick.status == TickStatus.FAILURE

        storage.update_tick(updated_tick)

        ticks = storage.get_ticks("my_sensor", "my_sensor")
        assert len(ticks) == 1
        tick = ticks[0]
        assert tick.tick_id > 0
        assert tick.instigator_name == "my_sensor"
        assert tick.timestamp == current_time
        assert tick.status == TickStatus.FAILURE
        assert tick.run_ids == []
        assert tick.error == error

    def test_purge_ticks(self, storage):
        assert storage

        if not self.can_purge():
            pytest.skip("Storage cannot purge")

        now = get_current_datetime()
        five_minutes_ago = (now - relativedelta(minutes=5)).timestamp()
        four_minutes_ago = (now - relativedelta(minutes=4)).timestamp()
        one_minute_ago = (now - relativedelta(minutes=1)).timestamp()
        storage.create_tick(self.build_sensor_tick(five_minutes_ago, TickStatus.SKIPPED))
        storage.create_tick(
            self.build_sensor_tick(four_minutes_ago, TickStatus.SUCCESS, run_id="fake_run_id")
        )
        one_minute_tick = storage.create_tick(
            self.build_sensor_tick(one_minute_ago, TickStatus.SKIPPED)
        )
        ticks = storage.get_ticks("my_sensor", "my_sensor")
        assert len(ticks) == 3

        latest_tick = ticks[0]
        assert latest_tick.tick_id == one_minute_tick.tick_id

        storage.purge_ticks(
            "my_sensor",
            "my_sensor",
            (now - relativedelta(minutes=2)).timestamp(),
            [TickStatus.SKIPPED],
        )

        ticks = storage.get_ticks("my_sensor", "my_sensor")
        assert len(ticks) == 2

    def test_ticks_filtered(self, storage):
        storage.create_tick(self.build_sensor_tick(time.time(), status=TickStatus.STARTED))
        storage.create_tick(self.build_sensor_tick(time.time(), status=TickStatus.SUCCESS))
        storage.create_tick(self.build_sensor_tick(time.time(), status=TickStatus.SKIPPED))
        storage.create_tick(
            self.build_sensor_tick(
                time.time(),
                status=TickStatus.FAILURE,
                error=SerializableErrorInfo(message="foobar", stack=[], cls_name=None, cause=None),
            )
        )

        ticks = storage.get_ticks("my_sensor", "my_sensor")
        assert len(ticks) == 4

        started = storage.get_ticks("my_sensor", "my_sensor", statuses=[TickStatus.STARTED])
        assert len(started) == 1

        successes = storage.get_ticks("my_sensor", "my_sensor", statuses=[TickStatus.SUCCESS])
        assert len(successes) == 1

        skips = storage.get_ticks("my_sensor", "my_sensor", statuses=[TickStatus.SKIPPED])
        assert len(skips) == 1

        failures = storage.get_ticks("my_sensor", "my_sensor", statuses=[TickStatus.FAILURE])
        assert len(failures) == 1

        # everything but skips
        non_skips = storage.get_ticks(
            "my_sensor",
            "my_sensor",
            statuses=[TickStatus.STARTED, TickStatus.SUCCESS, TickStatus.FAILURE],
        )
        assert len(non_skips) == 3

    def test_ticks_batched(self, storage):
        if not storage.supports_batch_queries:
            pytest.skip("storage cannot batch")

        _a = storage.create_tick(
            self.build_sensor_tick(time.time(), status=TickStatus.SUCCESS, name="sensor_one")
        )
        b = storage.create_tick(
            self.build_sensor_tick(time.time(), status=TickStatus.SUCCESS, name="sensor_one")
        )
        _c = storage.create_tick(
            self.build_sensor_tick(time.time(), status=TickStatus.SUCCESS, name="sensor_two")
        )
        d = storage.create_tick(
            self.build_sensor_tick(time.time(), status=TickStatus.SUCCESS, name="sensor_two")
        )

        ticks_by_origin = storage.get_batch_ticks(["sensor_one", "sensor_two"], limit=1)
        assert set(ticks_by_origin.keys()) == {"sensor_one", "sensor_two"}
        assert len(ticks_by_origin["sensor_one"]) == 1
        assert ticks_by_origin["sensor_one"][0].tick_id == b.tick_id
        assert ticks_by_origin["sensor_two"][0].tick_id == d.tick_id

    def test_auto_materialize_asset_evaluations(self, storage) -> None:
        if not self.can_store_auto_materialize_asset_evaluations():
            pytest.skip("Storage cannot store auto materialize asset evaluations")

        condition_snapshot = AutomationConditionNodeSnapshot(
            class_name="foo", description="bar", unique_id=""
        )

        for _ in range(2):  # test idempotency
            storage.add_auto_materialize_asset_evaluations(
                evaluation_id=10,
                asset_evaluations=[
                    AutomationConditionEvaluation(
                        condition_snapshot=condition_snapshot,
                        true_subset=SerializableEntitySubset(
                            key=AssetKey("asset_one"), value=False
                        ),
                        candidate_subset=SerializableEntitySubset(
                            key=AssetKey("asset_one"), value=False
                        ),
                        start_timestamp=0,
                        end_timestamp=1,
                        subsets_with_metadata=[],
                        child_evaluations=[],
                    ).with_run_ids(set()),
                    AutomationConditionEvaluation(
                        condition_snapshot=condition_snapshot,
                        true_subset=SerializableEntitySubset(key=AssetKey("asset_two"), value=True),
                        candidate_subset=SerializableEntitySubset(
                            key=AssetKey("asset_two"), value=True
                        ),
                        start_timestamp=0,
                        end_timestamp=1,
                        subsets_with_metadata=[
                            AssetSubsetWithMetadata(
                                subset=SerializableEntitySubset(
                                    key=AssetKey("asset_two"), value=True
                                ),
                                metadata={"foo": MetadataValue.text("bar")},
                            )
                        ],
                        child_evaluations=[],
                    ).with_run_ids(set()),
                ],
            )

            res = storage.get_auto_materialize_asset_evaluations(
                key=AssetKey("asset_one"), limit=100
            )
            assert len(res) == 1
            assert res[0].get_evaluation_with_run_ids().evaluation.key == AssetKey("asset_one")
            assert res[0].evaluation_id == 10
            assert res[0].get_evaluation_with_run_ids().evaluation.true_subset.size == 0

            res = storage.get_auto_materialize_asset_evaluations(
                key=AssetKey("asset_two"), limit=100
            )
            assert len(res) == 1
            assert res[0].get_evaluation_with_run_ids().evaluation.key == AssetKey("asset_two")
            assert res[0].evaluation_id == 10
            assert res[0].get_evaluation_with_run_ids().evaluation.true_subset.size == 1

            res = storage.get_auto_materialize_evaluations_for_evaluation_id(evaluation_id=10)

            assert len(res) == 2
            assert res[0].get_evaluation_with_run_ids().evaluation.key == AssetKey("asset_one")
            assert res[0].evaluation_id == 10
            assert res[0].get_evaluation_with_run_ids().evaluation.true_subset.size == 0

            assert res[1].get_evaluation_with_run_ids().evaluation.key == AssetKey("asset_two")
            assert res[1].evaluation_id == 10
            assert res[1].get_evaluation_with_run_ids().evaluation.true_subset.size == 1

        storage.add_auto_materialize_asset_evaluations(
            evaluation_id=11,
            asset_evaluations=[
                AutomationConditionEvaluation(
                    condition_snapshot=condition_snapshot,
                    start_timestamp=0,
                    end_timestamp=1,
                    true_subset=SerializableEntitySubset(key=AssetKey("asset_one"), value=True),
                    candidate_subset=SerializableEntitySubset(
                        key=AssetKey("asset_one"), value=True
                    ),
                    subsets_with_metadata=[],
                    child_evaluations=[],
                ).with_run_ids(set()),
            ],
        )

        res = storage.get_auto_materialize_asset_evaluations(key=AssetKey("asset_one"), limit=100)
        assert len(res) == 2
        assert res[0].evaluation_id == 11
        assert res[1].evaluation_id == 10

        res = storage.get_auto_materialize_asset_evaluations(key=AssetKey("asset_one"), limit=1)
        assert len(res) == 1
        assert res[0].evaluation_id == 11

        res = storage.get_auto_materialize_asset_evaluations(
            key=AssetKey("asset_one"), limit=1, cursor=11
        )
        assert len(res) == 1
        assert res[0].evaluation_id == 10

        # add a mix of keys - one that already is using the unique index and one that is not

        eval_one = AutomationConditionEvaluation(
            condition_snapshot=AutomationConditionNodeSnapshot(
                class_name="foo", description="bar", unique_id=""
            ),
            start_timestamp=0,
            end_timestamp=1,
            true_subset=SerializableEntitySubset(key=AssetKey("asset_one"), value=True),
            candidate_subset=SerializableEntitySubset(key=AssetKey("asset_one"), value=True),
            subsets_with_metadata=[],
            child_evaluations=[],
        ).with_run_ids(set())

        eval_asset_three = AutomationConditionEvaluation(
            condition_snapshot=AutomationConditionNodeSnapshot(
                class_name="foo", description="bar", unique_id=""
            ),
            start_timestamp=0,
            end_timestamp=1,
            true_subset=SerializableEntitySubset(key=AssetKey("asset_three"), value=True),
            candidate_subset=SerializableEntitySubset(key=AssetKey("asset_three"), value=True),
            subsets_with_metadata=[],
            child_evaluations=[],
        ).with_run_ids(set())

        storage.add_auto_materialize_asset_evaluations(
            evaluation_id=11,
            asset_evaluations=[
                eval_one,
                eval_asset_three,
            ],
        )

        res = storage.get_auto_materialize_asset_evaluations(key=AssetKey("asset_one"), limit=100)
        assert len(res) == 2
        assert res[0].evaluation_id == 11
        assert res[0].get_evaluation_with_run_ids().evaluation == eval_one.evaluation

        res = storage.get_auto_materialize_asset_evaluations(key=AssetKey("asset_three"), limit=100)

        assert len(res) == 1
        assert res[0].evaluation_id == 11
        assert res[0].get_evaluation_with_run_ids().evaluation == eval_asset_three.evaluation

    def test_auto_materialize_asset_evaluations_with_partitions(self, storage) -> None:
        if not self.can_store_auto_materialize_asset_evaluations():
            pytest.skip("Storage cannot store auto materialize asset evaluations")

        partitions_def = StaticPartitionsDefinition(["a", "b"])
        subset = partitions_def.empty_subset().with_partition_keys(["a"])
        asset_subset = SerializableEntitySubset(key=AssetKey("asset_two"), value=subset)
        asset_subset_with_metadata = AssetSubsetWithMetadata(
            subset=asset_subset,
            metadata={
                "foo": MetadataValue.text("bar"),
                "baz": MetadataValue.asset(AssetKey("asset_one")),
            },
        )

        storage.add_auto_materialize_asset_evaluations(
            evaluation_id=10,
            asset_evaluations=[
                AutomationConditionEvaluation(
                    condition_snapshot=AutomationConditionNodeSnapshot(
                        class_name="foo", description="bar", unique_id=""
                    ),
                    start_timestamp=0,
                    end_timestamp=1,
                    true_subset=asset_subset,
                    candidate_subset=asset_subset,
                    subsets_with_metadata=[asset_subset_with_metadata],
                    child_evaluations=[],
                ).with_run_ids(set()),
            ],
        )

        res = storage.get_auto_materialize_asset_evaluations(key=AssetKey("asset_two"), limit=100)
        assert len(res) == 1
        assert res[0].get_evaluation_with_run_ids().evaluation.key == AssetKey("asset_two")
        assert res[0].evaluation_id == 10
        assert res[0].get_evaluation_with_run_ids().evaluation.true_subset.size == 1

        assert (
            res[0].get_evaluation_with_run_ids().evaluation.subsets_with_metadata[0]
            == asset_subset_with_metadata
        )

    def test_automation_condition_evaluations_check_key(self, storage) -> None:
        if not self.can_store_auto_materialize_asset_evaluations():
            pytest.skip("Storage cannot store auto materialize asset evaluations")

        check_key = AssetCheckKey(AssetKey("asset_two"), "check_one")
        entity_subset = SerializableEntitySubset(key=check_key, value=True)

        storage.add_auto_materialize_asset_evaluations(
            evaluation_id=10,
            asset_evaluations=[
                AutomationConditionEvaluation(
                    condition_snapshot=AutomationConditionNodeSnapshot(
                        class_name="foo", description="bar", unique_id=""
                    ),
                    start_timestamp=0,
                    end_timestamp=1,
                    true_subset=entity_subset,
                    candidate_subset=entity_subset,
                    subsets_with_metadata=[],
                    child_evaluations=[],
                ).with_run_ids(set()),
            ],
        )

        res = storage.get_auto_materialize_asset_evaluations(key=check_key.asset_key, limit=100)
        assert len(res) == 0  # stored for the check key, not the asset key

        # this is expected to fail until the next PR in the stack
        res = storage.get_auto_materialize_asset_evaluations(key=check_key, limit=100)
        assert len(res) == 1

        assert res[0].key == check_key
        assert res[0].get_evaluation_with_run_ids().evaluation.key == check_key
        assert res[0].evaluation_id == 10
        assert res[0].get_evaluation_with_run_ids().evaluation.true_subset.size == 1

    def test_purge_asset_evaluations(self, storage) -> None:
        if not self.can_purge():
            pytest.skip("Storage cannot purge")

        storage.add_auto_materialize_asset_evaluations(
            evaluation_id=11,
            asset_evaluations=[
                AutomationConditionEvaluation(
                    condition_snapshot=AutomationConditionNodeSnapshot(
                        class_name="foo", description="bar", unique_id=""
                    ),
                    start_timestamp=0,
                    end_timestamp=1,
                    true_subset=SerializableEntitySubset(key=AssetKey("asset_one"), value=True),
                    candidate_subset=SerializableEntitySubset(
                        key=AssetKey("asset_one"), value=True
                    ),
                    subsets_with_metadata=[],
                    child_evaluations=[],
                ).with_run_ids(set()),
            ],
        )

        storage.purge_asset_evaluations(
            before=(get_current_datetime() - relativedelta(hours=10)).timestamp()
        )

        res = storage.get_auto_materialize_asset_evaluations(key=AssetKey("asset_one"), limit=100)
        assert len(res) == 1

        storage.purge_asset_evaluations(
            before=(get_current_datetime() + relativedelta(minutes=10)).timestamp()
        )

        res = storage.get_auto_materialize_asset_evaluations(key=AssetKey("asset_one"), limit=100)
        assert len(res) == 0
