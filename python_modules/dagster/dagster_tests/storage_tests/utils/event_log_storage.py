import datetime
import logging  # noqa: F401; used by mock in string form
import re
import sys
import time
from contextlib import ExitStack, contextmanager
from typing import List, Optional, Sequence, Tuple, cast

import mock
import pendulum
import pytest
from dagster import (
    AssetKey,
    AssetMaterialization,
    AssetObservation,
    DagsterInstance,
    EventLogRecord,
    EventRecordsFilter,
    Field,
    In,
    JobDefinition,
    Out,
    Output,
    RetryRequested,
    RunShardedEventsCursor,
    _check as check,
    _seven as seven,
    asset,
    in_process_executor,
    job,
    op,
    resource,
)
from dagster._core.assets import AssetDetails
from dagster._core.definitions import ExpectationResult
from dagster._core.definitions.dependency import NodeHandle
from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionKey
from dagster._core.definitions.pipeline_base import InMemoryPipeline
from dagster._core.events import (
    AssetMaterializationPlannedData,
    DagsterEvent,
    DagsterEventType,
    EngineEventData,
    StepExpectationResultData,
    StepMaterializationData,
)
from dagster._core.events.log import EventLogEntry, construct_event_logger
from dagster._core.execution.api import execute_run
from dagster._core.execution.plan.handle import StepHandle
from dagster._core.execution.plan.objects import StepFailureData, StepSuccessData
from dagster._core.execution.results import PipelineExecutionResult
from dagster._core.execution.stats import StepEventStatus
from dagster._core.host_representation.origin import (
    ExternalPipelineOrigin,
    ExternalRepositoryOrigin,
    InProcessRepositoryLocationOrigin,
)
from dagster._core.storage.event_log import InMemoryEventLogStorage, SqlEventLogStorage
from dagster._core.storage.event_log.base import EventLogStorage
from dagster._core.storage.event_log.migration import (
    EVENT_LOG_DATA_MIGRATIONS,
    migrate_asset_key_data,
)
from dagster._core.storage.event_log.sqlite.sqlite_event_log import SqliteEventLogStorage
from dagster._core.storage.partition_status_cache import AssetStatusCacheValue
from dagster._core.test_utils import create_run_for_test, instance_for_test
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.utils import make_new_run_id
from dagster._legacy import AssetGroup, build_assets_job
from dagster._loggers import colored_console_logger
from dagster._serdes.serdes import deserialize_value
from dagster._utils import datetime_as_float

TEST_TIMEOUT = 5

# py36 & 37 list.append not hashable
# pylint: disable=unnecessary-lambda


@contextmanager
def create_and_delete_test_runs(instance: DagsterInstance, run_ids: Sequence[str]):
    check.opt_inst_param(instance, "instance", DagsterInstance)
    check.sequence_param(run_ids, "run_ids", of_type=str)
    if instance:
        for run_id in run_ids:
            create_run_for_test(
                instance,
                run_id=run_id,
                external_pipeline_origin=ExternalPipelineOrigin(
                    ExternalRepositoryOrigin(
                        InProcessRepositoryLocationOrigin(
                            LoadableTargetOrigin(
                                executable_path=sys.executable,
                                module_name="fake",
                            )
                        ),
                        "fake",
                    ),
                    "fake",
                ),
            )
    yield
    if instance:
        for run_id in run_ids:
            instance.delete_run(run_id)


def create_test_event_log_record(message: str, run_id):
    return EventLogEntry(
        error_info=None,
        user_message=message,
        level="debug",
        run_id=run_id,
        timestamp=time.time(),
        dagster_event=DagsterEvent(
            DagsterEventType.ENGINE_EVENT.value,
            "nonce",
            event_specific_data=EngineEventData.in_process(999),
        ),
    )


def _stats_records(run_id):
    now = time.time()
    return [
        _event_record(run_id, "A", now - 325, DagsterEventType.STEP_START),
        _event_record(
            run_id,
            "A",
            now - 225,
            DagsterEventType.STEP_SUCCESS,
            StepSuccessData(duration_ms=100000.0),
        ),
        _event_record(run_id, "B", now - 225, DagsterEventType.STEP_START),
        _event_record(
            run_id,
            "B",
            now - 175,
            DagsterEventType.STEP_FAILURE,
            StepFailureData(error=None, user_failure_data=None),
        ),
        _event_record(run_id, "C", now - 175, DagsterEventType.STEP_START),
        _event_record(run_id, "C", now - 150, DagsterEventType.STEP_SKIPPED),
        _event_record(run_id, "D", now - 150, DagsterEventType.STEP_START),
        _event_record(
            run_id,
            "D",
            now - 125,
            DagsterEventType.ASSET_MATERIALIZATION,
            StepMaterializationData(AssetMaterialization(asset_key="mat_1")),
        ),
        _event_record(
            run_id,
            "D",
            now - 100,
            DagsterEventType.STEP_EXPECTATION_RESULT,
            StepExpectationResultData(ExpectationResult(success=True, label="exp 1")),
        ),
        _event_record(
            run_id,
            "D",
            now - 75,
            DagsterEventType.ASSET_MATERIALIZATION,
            StepMaterializationData(AssetMaterialization(asset_key="mat_2")),
        ),
        _event_record(
            run_id,
            "D",
            now - 50,
            DagsterEventType.STEP_EXPECTATION_RESULT,
            StepExpectationResultData(ExpectationResult(success=False, label="exp 2")),
        ),
        _event_record(
            run_id,
            "D",
            now - 25,
            DagsterEventType.ASSET_MATERIALIZATION,
            StepMaterializationData(AssetMaterialization(asset_key="mat_3")),
        ),
        _event_record(
            run_id,
            "D",
            now,
            DagsterEventType.STEP_SUCCESS,
            StepSuccessData(duration_ms=150000.0),
        ),
    ]


def _event_record(run_id, solid_name, timestamp, event_type, event_specific_data=None):
    pipeline_name = "pipeline_name"
    solid_handle = NodeHandle(solid_name, None)
    step_handle = StepHandle(solid_handle)
    return EventLogEntry(
        error_info=None,
        user_message="",
        level="debug",
        run_id=run_id,
        timestamp=timestamp,
        step_key=step_handle.to_key(),
        pipeline_name=pipeline_name,
        dagster_event=DagsterEvent(
            event_type.value,
            pipeline_name,
            solid_handle=solid_handle,
            step_handle=step_handle,
            event_specific_data=event_specific_data,
        ),
    )


def _default_resources():
    @resource
    def foo_resource():
        time.sleep(0.1)
        return "foo"

    return {"foo": foo_resource}


def _default_loggers(event_callback):
    return {
        "callback": construct_event_logger(event_callback),
        "console": colored_console_logger,
    }


# This exists to create synthetic events to test the store
def _synthesize_events(
    ops_fn, run_id=None, check_success=True, instance=None, run_config=None
) -> Tuple[List[EventLogEntry], PipelineExecutionResult]:
    events = []

    def _append_event(event):
        events.append(event)

    @job(
        resource_defs=_default_resources(),
        logger_defs=_default_loggers(_append_event),
        executor_def=in_process_executor,
    )
    def a_job():
        ops_fn()

    result = None

    with ExitStack() as stack:
        if not instance:
            instance = stack.enter_context(DagsterInstance.ephemeral())

        run_config = {
            **{"loggers": {"callback": {}, "console": {}}},
            **(run_config if run_config else {}),
        }

        pipeline_run = instance.create_run_for_pipeline(a_job, run_id=run_id, run_config=run_config)
        result = execute_run(InMemoryPipeline(a_job), pipeline_run, instance)

        if check_success:
            assert result.success

    assert result

    return events, result


def _fetch_all_events(configured_storage, run_id=None):
    with configured_storage.run_connection(run_id=run_id) as conn:
        res = conn.execute("SELECT event from event_logs")
        return res.fetchall()


def _event_types(out_events):
    return list(
        map(
            lambda e: e.dagster_event.event_type if e.dagster_event else None,
            out_events,
        )
    )


@op
def should_succeed(context):
    time.sleep(0.001)
    context.log.info("succeed")
    return "yay"


@op
def asset_op_one(_):
    yield AssetMaterialization(asset_key=AssetKey("asset_1"))
    yield Output(1)


@op
def asset_op_two(_):
    yield AssetMaterialization(asset_key=AssetKey("asset_2"))
    yield AssetMaterialization(asset_key=AssetKey(["path", "to", "asset_3"]))
    yield Output(1)


def one_asset_solid():
    asset_op_one()


def two_asset_ops():
    asset_op_one()
    asset_op_two()


@op
def return_one_op(_):
    return 1


def return_one_solid_func():
    return_one_op()


def cursor_datetime_args():
    # parametrization function to test constructing run-sharded event log cursors, with both
    # timezone-aware and timezone-naive datetimes
    yield None
    yield pendulum.now()
    yield datetime.datetime.now()


def _execute_job_and_store_events(
    instance: DagsterInstance,
    storage: EventLogStorage,
    job: JobDefinition,
    run_id: Optional[str] = None,
    asset_selection: Optional[Sequence[AssetKey]] = None,
    partition_key: Optional[str] = None,
):
    result = job.execute_in_process(
        instance=instance,
        raise_on_error=False,
        run_id=run_id,
        asset_selection=asset_selection,
        partition_key=partition_key,
    )
    events = instance.all_logs(run_id=result.run_id)
    for event in events:
        storage.store_event(event)
    return result


def _get_cached_status_for_asset(storage, asset_key):
    asset_records = list(storage.get_asset_records([asset_key]))
    assert len(asset_records) == 1
    return asset_records[0].asset_entry.cached_status


class TestEventLogStorage:
    """You can extend this class to easily run these set of tests on any event log storage. When extending,
    you simply need to override the `event_log_storage` fixture and return your implementation of
    `EventLogStorage`.

    For example:

    ```
    class TestMyStorageImplementation(TestEventLogStorage):
        __test__ = True

        @pytest.fixture(scope='function', name='storage')
        def event_log_storage(self):  # pylint: disable=arguments-differ
            return MyStorageImplementation()
    ```
    """

    __test__ = False

    @pytest.fixture(name="storage", params=[])
    def event_log_storage(self, request):
        with request.param() as s:
            try:
                yield s
            finally:
                s.dispose()

    @pytest.fixture(name="instance")
    def instance(self, request) -> Optional[DagsterInstance]:  # pylint: disable=unused-argument
        return None

    @pytest.fixture(scope="function", name="test_run_id")
    def create_run_and_get_run_id(self, instance):
        run_id = make_new_run_id()
        with create_and_delete_test_runs(instance, [run_id]):
            yield run_id

    def is_sqlite(self, storage):
        return isinstance(storage, SqliteEventLogStorage)

    def test_init_log_storage(self, storage):
        if isinstance(storage, InMemoryEventLogStorage):
            assert not storage.is_persistent
        else:
            assert storage.is_persistent

    def test_log_storage_run_not_found(self, storage):
        assert storage.get_logs_for_run("bar") == []

    def can_wipe(self):
        # Whether the storage is allowed to wipe the event log
        return True

    def can_watch(self):
        # Whether the storage is allowed to watch the event log
        return True

    def test_event_log_storage_store_events_and_wipe(self, test_run_id, storage):
        assert len(storage.get_logs_for_run(test_run_id)) == 0
        storage.store_event(
            EventLogEntry(
                error_info=None,
                level="debug",
                user_message="",
                run_id=test_run_id,
                timestamp=time.time(),
                dagster_event=DagsterEvent(
                    DagsterEventType.ENGINE_EVENT.value,
                    "nonce",
                    event_specific_data=EngineEventData.in_process(999),
                ),
            )
        )
        assert len(storage.get_logs_for_run(test_run_id)) == 1
        assert storage.get_stats_for_run(test_run_id)

        if self.can_wipe():
            storage.wipe()
            assert len(storage.get_logs_for_run(test_run_id)) == 0

    def test_event_log_storage_store_with_multiple_runs(self, instance, storage):
        runs = ["foo", "bar", "baz"]
        if instance:
            for run in runs:
                create_run_for_test(instance, run_id=run)
        for run_id in runs:
            assert len(storage.get_logs_for_run(run_id)) == 0
            storage.store_event(
                EventLogEntry(
                    error_info=None,
                    level="debug",
                    user_message="",
                    run_id=run_id,
                    timestamp=time.time(),
                    dagster_event=DagsterEvent(
                        DagsterEventType.STEP_SUCCESS.value,
                        "nonce",
                        event_specific_data=StepSuccessData(duration_ms=100.0),
                    ),
                )
            )

        for run_id in runs:
            assert len(storage.get_logs_for_run(run_id)) == 1
            assert storage.get_stats_for_run(run_id).steps_succeeded == 1

        if self.can_wipe():
            storage.wipe()
            for run_id in runs:
                assert len(storage.get_logs_for_run(run_id)) == 0

        if instance:
            for run in runs:
                instance.delete_run(run)

    def test_event_log_storage_watch(self, test_run_id, storage):
        if not self.can_watch():
            pytest.skip("storage cannot watch runs")

        watched = []
        watcher = lambda x, y: watched.append(x)  # pylint: disable=unnecessary-lambda

        assert len(storage.get_logs_for_run(test_run_id)) == 0

        storage.store_event(create_test_event_log_record(str(1), test_run_id))
        assert len(storage.get_logs_for_run(test_run_id)) == 1
        assert len(watched) == 0

        conn = storage.get_records_for_run(test_run_id)
        assert len(conn.records) == 1
        storage.watch(test_run_id, conn.cursor, watcher)

        storage.store_event(create_test_event_log_record(str(2), test_run_id))
        storage.store_event(create_test_event_log_record(str(3), test_run_id))
        storage.store_event(create_test_event_log_record(str(4), test_run_id))

        attempts = 10
        while len(watched) < 3 and attempts > 0:
            time.sleep(0.5)
            attempts -= 1
        assert len(watched) == 3

        assert len(storage.get_logs_for_run(test_run_id)) == 4

        storage.end_watch(test_run_id, watcher)
        time.sleep(0.3)  # this value scientifically selected from a range of attractive values
        storage.store_event(create_test_event_log_record(str(5), test_run_id))

        assert len(storage.get_logs_for_run(test_run_id)) == 5
        assert len(watched) == 3

        storage.delete_events(test_run_id)

        assert len(storage.get_logs_for_run(test_run_id)) == 0
        assert len(watched) == 3

        assert [int(evt.user_message) for evt in watched] == [2, 3, 4]

    def test_event_log_storage_pagination(self, test_run_id, instance, storage):
        with create_and_delete_test_runs(instance, ["other_run"]):
            # two runs events to ensure pagination is not affected by other runs
            storage.store_event(create_test_event_log_record("A", run_id=test_run_id))
            storage.store_event(create_test_event_log_record(str(0), run_id="other_run"))
            storage.store_event(create_test_event_log_record("B", run_id=test_run_id))
            storage.store_event(create_test_event_log_record(str(1), run_id="other_run"))
            storage.store_event(create_test_event_log_record("C", run_id=test_run_id))
            storage.store_event(create_test_event_log_record(str(2), run_id="other_run"))
            storage.store_event(create_test_event_log_record("D", run_id=test_run_id))

            assert len(storage.get_logs_for_run(test_run_id)) == 4
            assert len(storage.get_logs_for_run(test_run_id, -1)) == 4
            assert len(storage.get_logs_for_run(test_run_id, 0)) == 3
            assert len(storage.get_logs_for_run(test_run_id, 1)) == 2
            assert len(storage.get_logs_for_run(test_run_id, 2)) == 1
            assert len(storage.get_logs_for_run(test_run_id, 3)) == 0

    def test_event_log_delete(self, test_run_id, storage):
        assert len(storage.get_logs_for_run(test_run_id)) == 0
        storage.store_event(create_test_event_log_record(str(0), test_run_id))
        assert len(storage.get_logs_for_run(test_run_id)) == 1
        assert storage.get_stats_for_run(test_run_id)
        storage.delete_events(test_run_id)
        assert len(storage.get_logs_for_run(test_run_id)) == 0

    def test_event_log_get_stats_without_start_and_success(self, test_run_id, storage):
        # When an event log doesn't have a PIPELINE_START or PIPELINE_SUCCESS | PIPELINE_FAILURE event,
        # we want to ensure storage.get_stats_for_run(...) doesn't throw an error.
        assert len(storage.get_logs_for_run(test_run_id)) == 0
        assert storage.get_stats_for_run(test_run_id)

    def test_event_log_get_stats_for_run(self, test_run_id, storage):
        import math

        enqueued_time = time.time()
        launched_time = enqueued_time + 20
        start_time = launched_time + 50
        storage.store_event(
            EventLogEntry(
                error_info=None,
                level="debug",
                user_message="",
                run_id=test_run_id,
                timestamp=enqueued_time,
                dagster_event=DagsterEvent(
                    DagsterEventType.PIPELINE_ENQUEUED.value,
                    "nonce",
                ),
            )
        )
        storage.store_event(
            EventLogEntry(
                error_info=None,
                level="debug",
                user_message="",
                run_id=test_run_id,
                timestamp=launched_time,
                dagster_event=DagsterEvent(
                    DagsterEventType.PIPELINE_STARTING.value,
                    "nonce",
                ),
            )
        )
        storage.store_event(
            EventLogEntry(
                error_info=None,
                level="debug",
                user_message="",
                run_id=test_run_id,
                timestamp=start_time,
                dagster_event=DagsterEvent(
                    DagsterEventType.PIPELINE_START.value,
                    "nonce",
                ),
            )
        )
        assert math.isclose(storage.get_stats_for_run(test_run_id).enqueued_time, enqueued_time)
        assert math.isclose(storage.get_stats_for_run(test_run_id).launch_time, launched_time)
        assert math.isclose(storage.get_stats_for_run(test_run_id).start_time, start_time)

    def test_event_log_step_stats(self, test_run_id, storage):
        # When an event log doesn't have a PIPELINE_START or PIPELINE_SUCCESS | PIPELINE_FAILURE event,
        # we want to ensure storage.get_stats_for_run(...) doesn't throw an error.

        for record in _stats_records(run_id=test_run_id):
            storage.store_event(record)

        step_stats = storage.get_step_stats_for_run(test_run_id)
        assert len(step_stats) == 4

        a_stats = [stats for stats in step_stats if stats.step_key == "A"][0]
        assert a_stats.step_key == "A"
        assert a_stats.status.value == "SUCCESS"
        assert a_stats.end_time - a_stats.start_time == 100
        assert len(a_stats.attempts_list) == 1

        b_stats = [stats for stats in step_stats if stats.step_key == "B"][0]
        assert b_stats.step_key == "B"
        assert b_stats.status.value == "FAILURE"
        assert b_stats.end_time - b_stats.start_time == 50
        assert len(b_stats.attempts_list) == 1

        c_stats = [stats for stats in step_stats if stats.step_key == "C"][0]
        assert c_stats.step_key == "C"
        assert c_stats.status.value == "SKIPPED"
        assert c_stats.end_time - c_stats.start_time == 25
        assert len(c_stats.attempts_list) == 1

        d_stats = [stats for stats in step_stats if stats.step_key == "D"][0]
        assert d_stats.step_key == "D"
        assert d_stats.status.value == "SUCCESS"
        assert d_stats.end_time - d_stats.start_time == 150
        assert len(d_stats.materialization_events) == 3
        assert len(d_stats.expectation_results) == 2
        assert len(c_stats.attempts_list) == 1

    def test_secondary_index(self, storage):
        if not isinstance(storage, SqlEventLogStorage):
            pytest.skip("This test is for SQL-backed Event Log behavior")

        # test that newly initialized DBs will have the secondary indexes built
        for name in EVENT_LOG_DATA_MIGRATIONS.keys():
            assert storage.has_secondary_index(name)

        # test the generic API with garbage migration names
        assert not storage.has_secondary_index("_A")
        assert not storage.has_secondary_index("_B")
        storage.enable_secondary_index("_A")
        assert storage.has_secondary_index("_A")
        assert not storage.has_secondary_index("_B")
        storage.enable_secondary_index("_B")
        assert storage.has_secondary_index("_A")
        assert storage.has_secondary_index("_B")

    def test_basic_event_store(self, test_run_id, storage):
        from collections import Counter as CollectionsCounter

        if not isinstance(storage, SqlEventLogStorage):
            pytest.skip("This test is for SQL-backed Event Log behavior")

        events, _result = _synthesize_events(return_one_solid_func, run_id=test_run_id)

        for event in events:
            storage.store_event(event)

        rows = _fetch_all_events(storage, run_id=test_run_id)

        out_events = list(map(lambda r: deserialize_value(r[0], EventLogEntry), rows))

        # messages can come out of order
        event_type_counts = CollectionsCounter(_event_types(out_events))
        assert event_type_counts
        assert CollectionsCounter(_event_types(out_events)) == CollectionsCounter(
            _event_types(events)
        )

    def test_basic_get_logs_for_run(self, test_run_id, storage):
        events, result = _synthesize_events(return_one_solid_func, run_id=test_run_id)

        for event in events:
            storage.store_event(event)
        out_events = storage.get_logs_for_run(result.run_id)

        assert _event_types(out_events) == _event_types(events)

    def test_get_logs_for_run_cursor_limit(self, test_run_id, storage):
        events, result = _synthesize_events(return_one_solid_func, run_id=test_run_id)

        for event in events:
            storage.store_event(event)

        out_events = []
        cursor = -1
        fuse = 0
        chunk_size = 2
        while fuse < 50:
            fuse += 1
            # fetch in batches w/ limit & cursor
            chunk = storage.get_logs_for_run(result.run_id, cursor=cursor, limit=chunk_size)
            if not chunk:
                break
            assert len(chunk) <= chunk_size
            out_events += chunk
            cursor += len(chunk)

        assert _event_types(out_events) == _event_types(events)

    def test_wipe_sql_backed_event_log(self, test_run_id, storage):
        events, result = _synthesize_events(return_one_solid_func, run_id=test_run_id)

        for event in events:
            storage.store_event(event)

        out_events = storage.get_logs_for_run(result.run_id)

        assert _event_types(out_events) == _event_types(events)

        if self.can_wipe():
            storage.wipe()

            assert storage.get_logs_for_run(result.run_id) == []

    def test_delete_sql_backed_event_log(self, test_run_id, storage):
        events, result = _synthesize_events(return_one_solid_func, run_id=test_run_id)

        for event in events:
            storage.store_event(event)

        out_events = storage.get_logs_for_run(result.run_id)

        assert _event_types(out_events) == _event_types(events)

        storage.delete_events(result.run_id)

        assert storage.get_logs_for_run(result.run_id) == []

    def test_get_logs_for_run_of_type(self, test_run_id, storage):
        events, result = _synthesize_events(return_one_solid_func, run_id=test_run_id)

        for event in events:
            storage.store_event(event)

        assert _event_types(
            storage.get_logs_for_run(result.run_id, of_type=DagsterEventType.RUN_SUCCESS)
        ) == [DagsterEventType.RUN_SUCCESS]

        assert _event_types(
            storage.get_logs_for_run(result.run_id, of_type=DagsterEventType.STEP_SUCCESS)
        ) == [DagsterEventType.STEP_SUCCESS]

        assert _event_types(
            storage.get_logs_for_run(
                result.run_id,
                of_type={
                    DagsterEventType.STEP_SUCCESS,
                    DagsterEventType.RUN_SUCCESS,
                },
            )
        ) == [DagsterEventType.STEP_SUCCESS, DagsterEventType.RUN_SUCCESS]

    def test_basic_get_logs_for_run_cursor(self, test_run_id, storage):
        events, result = _synthesize_events(return_one_solid_func, run_id=test_run_id)

        for event in events:
            storage.store_event(event)

        assert _event_types(storage.get_logs_for_run(result.run_id, cursor=-1)) == _event_types(
            events
        )

    def test_basic_get_logs_for_run_multiple_runs(self, instance, storage):
        events_one, result_one = _synthesize_events(return_one_solid_func)
        events_two, result_two = _synthesize_events(return_one_solid_func)

        with create_and_delete_test_runs(instance, [result_one.run_id, result_two.run_id]):
            for event in events_one:
                storage.store_event(event)

            for event in events_two:
                storage.store_event(event)

            out_events_one = storage.get_logs_for_run(result_one.run_id)
            assert len(out_events_one) == len(events_one)

            assert set(_event_types(out_events_one)) == set(_event_types(events_one))

            assert set(map(lambda e: e.run_id, out_events_one)) == {result_one.run_id}

            stats_one = storage.get_stats_for_run(result_one.run_id)
            assert stats_one.steps_succeeded == 1

            out_events_two = storage.get_logs_for_run(result_two.run_id)
            assert len(out_events_two) == len(events_two)

            assert set(_event_types(out_events_two)) == set(_event_types(events_two))

            assert set(map(lambda e: e.run_id, out_events_two)) == {result_two.run_id}

            stats_two = storage.get_stats_for_run(result_two.run_id)
            assert stats_two.steps_succeeded == 1

    def test_basic_get_logs_for_run_multiple_runs_cursors(self, instance, storage):
        events_one, result_one = _synthesize_events(return_one_solid_func)
        events_two, result_two = _synthesize_events(return_one_solid_func)

        with create_and_delete_test_runs(instance, [result_one.run_id, result_two.run_id]):
            for event in events_one:
                storage.store_event(event)

            for event in events_two:
                storage.store_event(event)

            out_events_one = storage.get_logs_for_run(result_one.run_id, cursor=-1)
            assert len(out_events_one) == len(events_one)

            assert set(_event_types(out_events_one)) == set(_event_types(events_one))

            assert set(map(lambda e: e.run_id, out_events_one)) == {result_one.run_id}

            out_events_two = storage.get_logs_for_run(result_two.run_id, cursor=-1)
            assert len(out_events_two) == len(events_two)
            assert set(_event_types(out_events_two)) == set(_event_types(events_one))

            assert set(map(lambda e: e.run_id, out_events_two)) == {result_two.run_id}

    def test_event_watcher_single_run_event(self, storage, test_run_id):
        if not self.can_watch():
            pytest.skip("storage cannot watch runs")

        event_list = []

        storage.watch(test_run_id, None, lambda x, _y: event_list.append(x))

        events, _ = _synthesize_events(return_one_solid_func, run_id=test_run_id)
        for event in events:
            storage.store_event(event)

        start = time.time()
        while len(event_list) < len(events) and time.time() - start < TEST_TIMEOUT:
            time.sleep(0.01)

        assert len(event_list) == len(events)
        assert all([isinstance(event, EventLogEntry) for event in event_list])

    def test_event_watcher_filter_run_event(self, instance, storage):
        if not self.can_watch():
            pytest.skip("storage cannot watch runs")

        run_id_one = make_new_run_id()
        run_id_two = make_new_run_id()

        with create_and_delete_test_runs(instance, [run_id_one, run_id_two]):
            # only watch one of the runs
            event_list = []
            storage.watch(run_id_two, None, lambda x, _y: event_list.append(x))

            events_one, _result_one = _synthesize_events(return_one_solid_func, run_id=run_id_one)
            for event in events_one:
                storage.store_event(event)

            events_two, _result_two = _synthesize_events(return_one_solid_func, run_id=run_id_two)
            for event in events_two:
                storage.store_event(event)

            start = time.time()
            while len(event_list) < len(events_two) and time.time() - start < TEST_TIMEOUT:
                time.sleep(0.01)

            assert len(event_list) == len(events_two)
            assert all([isinstance(event, EventLogEntry) for event in event_list])

    def test_event_watcher_filter_two_runs_event(self, storage, instance):
        if not self.can_watch():
            pytest.skip("storage cannot watch runs")

        event_list_one = []
        event_list_two = []

        run_id_one = make_new_run_id()
        run_id_two = make_new_run_id()

        with create_and_delete_test_runs(instance, [run_id_one, run_id_two]):
            storage.watch(run_id_one, None, lambda x, _y: event_list_one.append(x))
            storage.watch(run_id_two, None, lambda x, _y: event_list_two.append(x))

            events_one, _result_one = _synthesize_events(return_one_solid_func, run_id=run_id_one)
            for event in events_one:
                storage.store_event(event)

            events_two, _result_two = _synthesize_events(return_one_solid_func, run_id=run_id_two)
            for event in events_two:
                storage.store_event(event)

            start = time.time()
            while (
                len(event_list_one) < len(events_one) or len(event_list_two) < len(events_two)
            ) and time.time() - start < TEST_TIMEOUT:
                pass

            assert len(event_list_one) == len(events_one)
            assert len(event_list_two) == len(events_two)
            assert all([isinstance(event, EventLogEntry) for event in event_list_one])
            assert all([isinstance(event, EventLogEntry) for event in event_list_two])

    def test_correct_timezone(self, test_run_id, storage):
        curr_time = time.time()

        event = EventLogEntry(
            error_info=None,
            level="debug",
            user_message="",
            run_id=test_run_id,
            timestamp=curr_time,
            dagster_event=DagsterEvent(
                DagsterEventType.PIPELINE_START.value,
                "nonce",
                event_specific_data=EngineEventData.in_process(999),
            ),
        )

        storage.store_event(event)

        logs = storage.get_logs_for_run(test_run_id)

        assert len(logs) == 1

        log = logs[0]

        stats = storage.get_stats_for_run(test_run_id)

        assert int(log.timestamp) == int(stats.start_time)
        assert int(log.timestamp) == int(curr_time)

    def test_asset_materialization(self, storage, test_run_id):
        asset_key = AssetKey(["path", "to", "asset_one"])

        @op
        def materialize_one(_):
            yield AssetMaterialization(
                asset_key=asset_key,
                metadata={
                    "text": "hello",
                    "json": {"hello": "world"},
                    "one_float": 1.0,
                    "one_int": 1,
                },
            )
            yield Output(1)

        def _ops():
            materialize_one()

        with instance_for_test() as created_instance:
            if not storage.has_instance:
                storage.register_instance(created_instance)

            events_one, _ = _synthesize_events(_ops, instance=created_instance, run_id=test_run_id)

            for event in events_one:
                storage.store_event(event)

            assert asset_key in set(storage.all_asset_keys())

            records = storage.get_event_records(
                EventRecordsFilter(
                    event_type=DagsterEventType.ASSET_MATERIALIZATION,
                    asset_key=asset_key,
                )
            )
            assert len(records) == 1
            record = records[0]
            assert isinstance(record, EventLogRecord)
            assert record.event_log_entry.dagster_event.asset_key == asset_key

    def test_asset_events_error_parsing(self, storage):
        if not isinstance(storage, SqlEventLogStorage):
            pytest.skip("This test is for SQL-backed Event Log behavior")
        _logs = []

        def mock_log(msg, *_args, **_kwargs):
            _logs.append(msg)

        asset_key = AssetKey("asset_one")

        @op
        def materialize_one(_):
            yield AssetMaterialization(asset_key=asset_key)
            yield Output(1)

        def _ops():
            materialize_one()

        with instance_for_test() as instance:
            if not storage.has_instance:
                storage.register_instance(instance)
            events_one, _ = _synthesize_events(_ops, instance=instance)
            for event in events_one:
                storage.store_event(event)

            with ExitStack() as stack:
                stack.enter_context(
                    mock.patch(
                        "dagster._core.storage.event_log.sql_event_log.logging.warning",
                        side_effect=mock_log,
                    )
                )
                # for generic sql-based event log storage
                stack.enter_context(
                    mock.patch(
                        "dagster._core.storage.event_log.sql_event_log.deserialize_value",
                        return_value="not_an_event_record",
                    )
                )
                # for sqlite event log storage, which overrides the record fetching implementation
                stack.enter_context(
                    mock.patch(
                        "dagster._core.storage.event_log.sqlite.sqlite_event_log.deserialize_value",
                        return_value="not_an_event_record",
                    )
                )

                assert asset_key in set(storage.all_asset_keys())
                _records = storage.get_event_records(
                    EventRecordsFilter(
                        event_type=DagsterEventType.ASSET_MATERIALIZATION,
                        asset_key=asset_key,
                    )
                )
                assert len(_logs) == 1
                assert re.match("Could not resolve event record as EventLogEntry", _logs[0])

            with ExitStack() as stack:
                _logs = []  # reset logs
                stack.enter_context(
                    mock.patch(
                        "dagster._core.storage.event_log.sql_event_log.logging.warning",
                        side_effect=mock_log,
                    )
                )

                # for generic sql-based event log storage
                stack.enter_context(
                    mock.patch(
                        "dagster._core.storage.event_log.sql_event_log.deserialize_value",
                        side_effect=seven.JSONDecodeError("error", "", 0),
                    )
                )
                # for sqlite event log storage, which overrides the record fetching implementation
                stack.enter_context(
                    mock.patch(
                        "dagster._core.storage.event_log.sqlite.sqlite_event_log.deserialize_value",
                        side_effect=seven.JSONDecodeError("error", "", 0),
                    )
                )
                assert asset_key in set(storage.all_asset_keys())
                _records = storage.get_event_records(
                    EventRecordsFilter(
                        event_type=DagsterEventType.ASSET_MATERIALIZATION,
                        asset_key=asset_key,
                    )
                )
                assert len(_logs) == 1
                assert re.match("Could not parse event record id", _logs[0])

    def test_secondary_index_asset_keys(self, storage, instance):
        asset_key_one = AssetKey(["one"])
        asset_key_two = AssetKey(["two"])

        run_id_1 = make_new_run_id()
        run_id_2 = make_new_run_id()

        @op
        def materialize_one(_):
            yield AssetMaterialization(asset_key=asset_key_one)
            yield Output(1)

        @op
        def materialize_two(_):
            yield AssetMaterialization(asset_key=asset_key_two)
            yield Output(1)

        def _one():
            materialize_one()

        def _two():
            materialize_two()

        with create_and_delete_test_runs(instance, [run_id_1, run_id_2]):
            events_one, _ = _synthesize_events(_one, run_id=run_id_1)
            for event in events_one:
                storage.store_event(event)

            asset_keys = storage.all_asset_keys()
            assert len(asset_keys) == 1
            assert asset_key_one in set(asset_keys)
            migrate_asset_key_data(storage)
            asset_keys = storage.all_asset_keys()
            assert len(asset_keys) == 1
            assert asset_key_one in set(asset_keys)
            events_two, _ = _synthesize_events(_two, run_id=run_id_2)
            for event in events_two:
                storage.store_event(event)
            asset_keys = storage.all_asset_keys()
            assert len(asset_keys) == 2
            assert asset_key_one in set(asset_keys)
            assert asset_key_two in set(asset_keys)

    def test_run_step_stats(self, storage, test_run_id):
        @op(
            ins={"_input": In(str)},
            out=Out(str),
        )
        def should_fail(context, _input):
            context.log.info("fail")
            raise Exception("booo")

        def _one():
            should_fail(should_succeed())

        events, result = _synthesize_events(_one, check_success=False, run_id=test_run_id)
        for event in events:
            storage.store_event(event)

        step_stats = sorted(storage.get_step_stats_for_run(result.run_id), key=lambda x: x.end_time)
        assert len(step_stats) == 2
        assert step_stats[0].step_key == "should_succeed"
        assert step_stats[0].status == StepEventStatus.SUCCESS
        assert step_stats[0].end_time > step_stats[0].start_time
        assert step_stats[0].attempts == 1
        assert len(step_stats[0].attempts_list) == 1
        assert step_stats[1].step_key == "should_fail"
        assert step_stats[1].status == StepEventStatus.FAILURE
        assert step_stats[1].end_time > step_stats[0].start_time
        assert step_stats[1].attempts == 1
        assert len(step_stats[1].attempts_list) == 1

    def test_run_step_stats_with_retries(self, storage, test_run_id):
        @op(
            ins={"_input": In(str)},
            out=Out(str),
        )
        def should_retry(_, _input):
            time.sleep(0.001)
            raise RetryRequested(max_retries=3)

        def _one():
            should_retry(should_succeed())

        events, result = _synthesize_events(_one, check_success=False, run_id=test_run_id)
        for event in events:
            storage.store_event(event)

        step_stats = storage.get_step_stats_for_run(result.run_id, step_keys=["should_retry"])
        assert len(step_stats) == 1
        assert step_stats[0].step_key == "should_retry"
        assert step_stats[0].status == StepEventStatus.FAILURE
        assert step_stats[0].end_time > step_stats[0].start_time
        assert step_stats[0].attempts == 4
        assert len(step_stats[0].attempts_list) == 4

    # After adding the IN_PROGRESS field to the StepEventStatus enum, tests in internal fail
    # Temporarily skipping this test
    @pytest.mark.skip
    def test_run_step_stats_with_in_progress(self, test_run_id, storage):
        def _in_progress_run_records(run_id):
            now = time.time()
            return [
                _event_record(run_id, "A", now - 325, DagsterEventType.STEP_START),
                _event_record(run_id, "C", now - 175, DagsterEventType.STEP_START),
                _event_record(run_id, "C", now - 150, DagsterEventType.STEP_SKIPPED),
                _event_record(run_id, "D", now - 150, DagsterEventType.STEP_START),
                _event_record(run_id, "D", now - 150, DagsterEventType.STEP_UP_FOR_RETRY),
                _event_record(run_id, "E", now - 150, DagsterEventType.STEP_START),
                _event_record(run_id, "E", now - 150, DagsterEventType.STEP_UP_FOR_RETRY),
                _event_record(run_id, "E", now - 125, DagsterEventType.STEP_RESTARTED),
            ]

        for record in _in_progress_run_records(run_id=test_run_id):
            storage.store_event(record)

        step_stats = storage.get_step_stats_for_run(test_run_id)

        assert len(step_stats) == 4

        assert step_stats[0].step_key == "A"
        assert step_stats[0].status == StepEventStatus.IN_PROGRESS
        assert not step_stats[0].end_time
        assert step_stats[0].attempts == 1
        assert len(step_stats[0].attempts_list) == 1

        assert step_stats[1].step_key == "C"
        assert step_stats[1].status == StepEventStatus.SKIPPED
        assert step_stats[1].end_time > step_stats[1].start_time
        assert step_stats[1].attempts == 1
        assert len(step_stats[1].attempts_list) == 1

        assert step_stats[2].step_key == "D"
        assert step_stats[2].status == StepEventStatus.IN_PROGRESS
        assert not step_stats[2].end_time
        assert step_stats[2].attempts == 1
        assert len(step_stats[2].attempts_list) == 1

        assert step_stats[3].step_key == "E"
        assert step_stats[3].status == StepEventStatus.IN_PROGRESS
        assert not step_stats[3].end_time
        assert step_stats[3].attempts == 2
        assert len(step_stats[3].attempts_list) == 2

    def test_run_step_stats_with_resource_markers(self, storage, test_run_id):
        @op(required_resource_keys={"foo"})
        def foo_op():
            time.sleep(0.001)

        def _pipeline():
            foo_op()

        events, result = _synthesize_events(_pipeline, check_success=False, run_id=test_run_id)
        for event in events:
            storage.store_event(event)

        step_stats = storage.get_step_stats_for_run(result.run_id)
        assert len(step_stats) == 1
        assert step_stats[0].step_key == "foo_op"
        assert step_stats[0].status == StepEventStatus.SUCCESS
        assert step_stats[0].end_time > step_stats[0].start_time
        assert len(step_stats[0].markers) == 1
        assert step_stats[0].markers[0].end_time >= step_stats[0].markers[0].start_time + 0.1

    @pytest.mark.parametrize(
        "cursor_dt", cursor_datetime_args()
    )  # test both tz-aware and naive datetimes
    def test_get_event_records(self, storage, instance, cursor_dt):
        if self.is_sqlite(storage):
            # test sqlite in test_get_event_records_sqlite
            pytest.skip()

        asset_key = AssetKey(["path", "to", "asset_one"])

        @op
        def materialize_one(_):
            yield AssetMaterialization(
                asset_key=asset_key,
                metadata={
                    "text": "hello",
                    "json": {"hello": "world"},
                    "one_float": 1.0,
                    "one_int": 1,
                },
            )
            yield Output(1)

        def _ops():
            materialize_one()

        def _store_run_events(run_id):
            events, _ = _synthesize_events(_ops, run_id=run_id)
            for event in events:
                storage.store_event(event)

        # store events for three runs
        [run_id_1, run_id_2, run_id_3] = [
            make_new_run_id(),
            make_new_run_id(),
            make_new_run_id(),
        ]

        with create_and_delete_test_runs(instance, [run_id_1, run_id_2, run_id_3]):
            _store_run_events(run_id_1)
            _store_run_events(run_id_2)
            _store_run_events(run_id_3)

            all_success_events = storage.get_event_records(
                EventRecordsFilter(event_type=DagsterEventType.RUN_SUCCESS)
            )

            assert len(all_success_events) == 3
            min_success_record_id = all_success_events[-1].storage_id

            # after cursor
            def _build_cursor(record_id_cursor, run_cursor_dt):
                if not run_cursor_dt:
                    return record_id_cursor
                return RunShardedEventsCursor(id=record_id_cursor, run_updated_after=run_cursor_dt)

            assert not list(
                filter(
                    lambda r: r.storage_id <= min_success_record_id,
                    storage.get_event_records(
                        EventRecordsFilter(
                            event_type=DagsterEventType.RUN_SUCCESS,
                            after_cursor=_build_cursor(min_success_record_id, cursor_dt),
                        )
                    ),
                )
            )
            assert [
                i.storage_id
                for i in storage.get_event_records(
                    EventRecordsFilter(
                        event_type=DagsterEventType.RUN_SUCCESS,
                        after_cursor=_build_cursor(min_success_record_id, cursor_dt),
                    ),
                    ascending=True,
                    limit=2,
                )
            ] == [record.storage_id for record in all_success_events[:2][::-1]]

            assert set(_event_types([r.event_log_entry for r in all_success_events])) == {
                DagsterEventType.RUN_SUCCESS
            }

    def test_get_event_records_sqlite(self, storage):
        if not self.is_sqlite(storage):
            pytest.skip()

        asset_key = AssetKey(["path", "to", "asset_one"])

        events = []

        def _append_event(event):
            events.append(event)

        @op
        def materialize_one(_):
            yield AssetMaterialization(
                asset_key=asset_key,
                metadata={
                    "text": "hello",
                    "json": {"hello": "world"},
                    "one_float": 1.0,
                    "one_int": 1,
                },
            )
            yield Output(1)

        @job(
            resource_defs=_default_resources(),
            logger_defs=_default_loggers(_append_event),
            executor_def=in_process_executor,
        )
        def a_job():
            materialize_one()

        with instance_for_test() as instance:
            if not storage.has_instance:
                storage.register_instance(instance)

            # first run
            execute_run(
                InMemoryPipeline(a_job),
                instance.create_run_for_pipeline(
                    a_job,
                    run_id="1",
                    run_config={"loggers": {"callback": {}, "console": {}}},
                ),
                instance,
            )

            for event in events:
                storage.store_event(event)

            run_records = instance.get_run_records()
            assert len(run_records) == 1

            # second run
            events = []
            execute_run(
                InMemoryPipeline(a_job),
                instance.create_run_for_pipeline(
                    a_job,
                    run_id="2",
                    run_config={"loggers": {"callback": {}, "console": {}}},
                ),
                instance,
            )
            run_records = instance.get_run_records()
            assert len(run_records) == 2
            for event in events:
                storage.store_event(event)

            # third run
            events = []
            execute_run(
                InMemoryPipeline(a_job),
                instance.create_run_for_pipeline(
                    a_job,
                    run_id="3",
                    run_config={"loggers": {"callback": {}, "console": {}}},
                ),
                instance,
            )
            run_records = instance.get_run_records()
            assert len(run_records) == 3
            for event in events:
                storage.store_event(event)

            update_timestamp = run_records[-1].update_timestamp
            tzaware_dt = pendulum.from_timestamp(datetime_as_float(update_timestamp), tz="UTC")

            # use tz-aware cursor
            filtered_records = storage.get_event_records(
                EventRecordsFilter(
                    event_type=DagsterEventType.RUN_SUCCESS,
                    after_cursor=RunShardedEventsCursor(
                        id=0, run_updated_after=tzaware_dt
                    ),  # events after first run
                ),
                ascending=True,
            )
            assert len(filtered_records) == 2
            assert _event_types([r.event_log_entry for r in filtered_records]) == [
                DagsterEventType.RUN_SUCCESS,
                DagsterEventType.RUN_SUCCESS,
            ]
            assert [r.event_log_entry.run_id for r in filtered_records] == ["2", "3"]

            # use tz-naive cursor
            filtered_records = storage.get_event_records(
                EventRecordsFilter(
                    event_type=DagsterEventType.RUN_SUCCESS,
                    after_cursor=RunShardedEventsCursor(
                        id=0, run_updated_after=tzaware_dt.naive()
                    ),  # events after first run
                ),
                ascending=True,
            )
            assert len(filtered_records) == 2
            assert _event_types([r.event_log_entry for r in filtered_records]) == [
                DagsterEventType.RUN_SUCCESS,
                DagsterEventType.RUN_SUCCESS,
            ]
            assert [r.event_log_entry.run_id for r in filtered_records] == ["2", "3"]

            # use invalid cursor
            with pytest.raises(
                Exception, match="Add a RunShardedEventsCursor to your query filter"
            ):
                storage.get_event_records(
                    EventRecordsFilter(
                        event_type=DagsterEventType.RUN_SUCCESS,
                        after_cursor=0,
                    ),
                )

    def test_watch_exc_recovery(self, storage):
        if not self.can_watch():
            pytest.skip("storage cannot watch runs")

        # test that an exception in one watch doesn't fail out others

        err_run_id = make_new_run_id()
        safe_run_id = make_new_run_id()

        class CBException(Exception):
            pass

        def _throw(_x, _y):
            raise CBException("problem in watch callback")

        err_events, _ = _synthesize_events(return_one_solid_func, run_id=err_run_id)
        safe_events, _ = _synthesize_events(return_one_solid_func, run_id=safe_run_id)

        event_list = []

        storage.watch(err_run_id, None, _throw)
        storage.watch(safe_run_id, None, lambda x, _y: event_list.append(x))

        for event in err_events:
            storage.store_event(event)

        storage.end_watch(err_run_id, _throw)

        for event in safe_events:
            storage.store_event(event)

        start = time.time()
        while len(event_list) < len(safe_events) and time.time() - start < TEST_TIMEOUT:
            time.sleep(0.01)

        assert len(event_list) == len(safe_events)
        assert all([isinstance(event, EventLogEntry) for event in event_list])

    # https://github.com/dagster-io/dagster/issues/5127
    @pytest.mark.skip
    def test_watch_unwatch(self, storage):
        if not self.can_watch():
            pytest.skip("storage cannot watch runs")

        # test for dead lock bug

        err_run_id = make_new_run_id()
        safe_run_id = make_new_run_id()

        def _unsub(_x, _y):
            storage.end_watch(err_run_id, _unsub)

        err_events, _ = _synthesize_events(return_one_solid_func, run_id=err_run_id)
        safe_events, _ = _synthesize_events(return_one_solid_func, run_id=safe_run_id)

        event_list = []

        # Direct end_watch emulates behavior of clean up on exception downstream
        # of the subscription in the dagit webserver.
        storage.watch(err_run_id, None, _unsub)

        # Other active watches should proceed correctly.
        storage.watch(safe_run_id, None, lambda x, _y: event_list.append(x))

        for event in err_events:
            storage.store_event(event)

        for event in safe_events:
            storage.store_event(event)

        start = time.time()
        while len(event_list) < len(safe_events) and time.time() - start < TEST_TIMEOUT:
            time.sleep(0.01)

        assert len(event_list) == len(safe_events)
        assert all([isinstance(event, EventLogEntry) for event in event_list])

    def test_engine_event_markers(self, storage):
        @op
        def return_one(_):
            return 1

        @job
        def a_job():
            return_one()

        with instance_for_test() as instance:
            if not storage.has_instance:
                storage.register_instance(instance)

            run_id = make_new_run_id()
            run = instance.create_run_for_pipeline(a_job, run_id=run_id)

            instance.report_engine_event(
                "blah blah",
                run,
                EngineEventData(marker_start="FOO"),
                step_key="return_one",
            )
            instance.report_engine_event(
                "blah blah",
                run,
                EngineEventData(marker_end="FOO"),
                step_key="return_one",
            )
            logs = storage.get_logs_for_run(run_id)
            for entry in logs:
                assert entry.step_key == "return_one"

    def test_latest_materializations(self, storage, instance):
        @op
        def one(_):
            yield AssetMaterialization(AssetKey("a"), partition="1")
            yield AssetMaterialization(AssetKey("b"), partition="1")
            yield AssetMaterialization(AssetKey("c"), partition="1")
            yield AssetMaterialization(AssetKey("d"), partition="1")
            yield AssetObservation(AssetKey("a"), metadata={"foo": "bar"})
            yield Output(1)

        @op
        def two(_):
            yield AssetMaterialization(AssetKey("b"), partition="2")
            yield AssetMaterialization(AssetKey("c"), partition="2")
            yield Output(2)

        def _event_partition(event):
            assert event.dagster_event_type == DagsterEventType.ASSET_MATERIALIZATION
            return event.dagster_event.step_materialization_data.materialization.partition

        def _fetch_events(storage):
            return storage.get_latest_materialization_events(
                [
                    AssetKey("a"),
                    AssetKey("b"),
                    AssetKey("c"),
                    AssetKey("d"),
                ]
            )

        run_id_1 = make_new_run_id()
        run_id_2 = make_new_run_id()

        with create_and_delete_test_runs(instance, [run_id_1, run_id_2]):
            events, _ = _synthesize_events(lambda: one(), run_id_1)
            for event in events:
                storage.store_event(event)

            events_by_key = _fetch_events(storage)
            assert len(events_by_key) == 4

            # wipe 2 of the assets, make sure we respect that
            if self.can_wipe():
                storage.wipe_asset(AssetKey("a"))
                storage.wipe_asset(AssetKey("b"))
                events_by_key = _fetch_events(storage)
                assert events_by_key.get(AssetKey("a")) is None
                assert events_by_key.get(AssetKey("b")) is None

                # rematerialize one of the wiped assets, one of the existing assets
                events, _ = _synthesize_events(lambda: two(), run_id=run_id_2)
                for event in events:
                    storage.store_event(event)

                events_by_key = _fetch_events(storage)
                assert events_by_key.get(AssetKey("a")) is None

            else:
                events, _ = _synthesize_events(lambda: two(), run_id=run_id_2)
                for event in events:
                    storage.store_event(event)
                events_by_key = _fetch_events(storage)

    def test_asset_keys(self, storage, instance):
        with instance_for_test() as created_instance:
            if not storage.has_instance:
                storage.register_instance(created_instance)

            events_one, result1 = _synthesize_events(
                lambda: one_asset_solid(), instance=created_instance
            )
            events_two, result2 = _synthesize_events(
                lambda: two_asset_ops(), instance=created_instance
            )

            with create_and_delete_test_runs(instance, [result1.run_id, result2.run_id]):
                for event in events_one + events_two:
                    storage.store_event(event)

                asset_keys = storage.all_asset_keys()
                assert len(asset_keys) == 3
                assert set([asset_key.to_string() for asset_key in asset_keys]) == set(
                    ['["asset_1"]', '["asset_2"]', '["path", "to", "asset_3"]']
                )

    def test_has_asset_key(self, storage, instance):
        with instance_for_test() as created_instance:
            if not storage.has_instance:
                storage.register_instance(created_instance)

            events_one, result_1 = _synthesize_events(
                lambda: one_asset_solid(), instance=created_instance
            )
            events_two, result_2 = _synthesize_events(
                lambda: two_asset_ops(), instance=created_instance
            )

            with create_and_delete_test_runs(instance, [result_1.run_id, result_2.run_id]):
                for event in events_one + events_two:
                    storage.store_event(event)

                assert storage.has_asset_key(AssetKey(["path", "to", "asset_3"]))
                assert not storage.has_asset_key(AssetKey(["path", "to", "bogus", "asset"]))

    def test_asset_run_ids(self, storage, instance):
        with instance_for_test() as created_instance:
            if not storage.has_instance:
                storage.register_instance(created_instance)

            one_run_id = "one"
            two_run_id = "two"

            one_events, _ = _synthesize_events(
                lambda: one_asset_solid(), run_id=one_run_id, instance=created_instance
            )
            two_events, _ = _synthesize_events(
                lambda: two_asset_ops(), run_id=two_run_id, instance=created_instance
            )

            with create_and_delete_test_runs(instance, [one_run_id, two_run_id]):
                for event in one_events + two_events:
                    storage.store_event(event)

                run_ids = storage.get_asset_run_ids(AssetKey("asset_1"))
                assert set(run_ids) == set([one_run_id, two_run_id])

    def test_asset_normalization(self, storage, test_run_id):
        with instance_for_test() as instance:
            if not storage.has_instance:
                storage.register_instance(instance)

            @op
            def op_normalization(_):
                yield AssetMaterialization(asset_key="path/to-asset_4")
                yield Output(1)

            events, _ = _synthesize_events(
                lambda: op_normalization(), instance=instance, run_id=test_run_id
            )
            for event in events:
                storage.store_event(event)

            asset_keys = storage.all_asset_keys()
            assert len(asset_keys) == 1
            asset_key = asset_keys[0]
            assert asset_key.to_string() == '["path", "to", "asset_4"]'
            assert asset_key.path == ["path", "to", "asset_4"]

    def test_asset_wipe(self, storage, instance):
        with instance_for_test() as created_instance:
            if not storage.has_instance:
                storage.register_instance(created_instance)

            one_run_id = "one_run_id"
            two_run_id = "two_run_id"
            events_one, _ = _synthesize_events(
                lambda: one_asset_solid(), run_id=one_run_id, instance=created_instance
            )
            events_two, _ = _synthesize_events(
                lambda: two_asset_ops(), run_id=two_run_id, instance=created_instance
            )

            with create_and_delete_test_runs(instance, [one_run_id, two_run_id]):
                for event in events_one + events_two:
                    storage.store_event(event)

                asset_keys = storage.all_asset_keys()
                assert len(asset_keys) == 3
                assert storage.has_asset_key(AssetKey("asset_1"))
                asset_run_ids = storage.get_asset_run_ids(AssetKey("asset_1"))
                assert set(asset_run_ids) == set([one_run_id, two_run_id])

                log_count = len(storage.get_logs_for_run(one_run_id))
                if self.can_wipe():
                    for asset_key in asset_keys:
                        storage.wipe_asset(asset_key)

                    asset_keys = storage.all_asset_keys()
                    assert len(asset_keys) == 0
                    assert not storage.has_asset_key(AssetKey("asset_1"))
                    asset_run_ids = storage.get_asset_run_ids(AssetKey("asset_1"))
                    assert set(asset_run_ids) == set()
                    assert log_count == len(storage.get_logs_for_run(one_run_id))

                    one_run_id = "one_run_id_2"
                    events_one, _ = _synthesize_events(
                        lambda: one_asset_solid(),
                        run_id=one_run_id,
                        instance=created_instance,
                    )
                    with create_and_delete_test_runs(instance, [one_run_id]):
                        for event in events_one:
                            storage.store_event(event)

                        asset_keys = storage.all_asset_keys()
                        assert len(asset_keys) == 1
                        assert storage.has_asset_key(AssetKey("asset_1"))
                        asset_run_ids = storage.get_asset_run_ids(AssetKey("asset_1"))
                        assert set(asset_run_ids) == set([one_run_id])

    def test_asset_secondary_index(self, storage, instance):
        with instance_for_test() as created_instance:
            if not storage.has_instance:
                storage.register_instance(created_instance)

            events_one, result = _synthesize_events(
                lambda: one_asset_solid(), instance=created_instance
            )

            with create_and_delete_test_runs(instance, [result.run_id]):
                for event in events_one:
                    storage.store_event(event)

                asset_keys = storage.all_asset_keys()
                assert len(asset_keys) == 1
                migrate_asset_key_data(storage)

                two_first_run_id = "first"
                two_second_run_id = "second"
                events_two, _ = _synthesize_events(
                    lambda: two_asset_ops(),
                    run_id=two_first_run_id,
                    instance=created_instance,
                )
                events_two_two, _ = _synthesize_events(
                    lambda: two_asset_ops(),
                    run_id=two_second_run_id,
                    instance=created_instance,
                )

                with create_and_delete_test_runs(instance, [two_first_run_id, two_second_run_id]):
                    for event in events_two + events_two_two:
                        storage.store_event(event)

                    asset_keys = storage.all_asset_keys()
                    assert len(asset_keys) == 3

                    storage.delete_events(two_first_run_id)
                    asset_keys = storage.all_asset_keys()
                    assert len(asset_keys) == 3

                    storage.delete_events(two_second_run_id)
                    asset_keys = storage.all_asset_keys()
                    assert len(asset_keys) == 1

    def test_asset_partition_query(self, storage, instance):
        @op(config_schema={"partition": Field(str, is_required=False)})
        def op_partitioned(context):
            yield AssetMaterialization(
                asset_key=AssetKey("asset_key"),
                partition=context.op_config.get("partition"),
            )
            yield Output(1)

        with instance_for_test() as created_instance:
            if not storage.has_instance:
                storage.register_instance(created_instance)

            get_partitioned_config = lambda partition: {
                "ops": {"op_partitioned": {"config": {"partition": partition}}}
            }

            partitions = ["a", "a", "b", "c"]
            run_ids = [make_new_run_id() for _ in partitions]
            with create_and_delete_test_runs(instance, run_ids):
                for partition, run_id in zip([f"partition_{x}" for x in partitions], run_ids):
                    run_events, _ = _synthesize_events(
                        lambda: op_partitioned(),
                        instance=created_instance,
                        run_config=get_partitioned_config(partition),
                        run_id=run_id,
                    )
                    for event in run_events:
                        storage.store_event(event)

                records = storage.get_event_records(
                    EventRecordsFilter(
                        event_type=DagsterEventType.ASSET_MATERIALIZATION,
                        asset_key=AssetKey("asset_key"),
                    )
                )
                assert len(records) == 4

                records = storage.get_event_records(
                    EventRecordsFilter(
                        event_type=DagsterEventType.ASSET_MATERIALIZATION,
                        asset_key=AssetKey("asset_key"),
                        asset_partitions=["partition_a", "partition_b"],
                    )
                )
                assert len(records) == 3

    def test_get_asset_keys(self, storage, test_run_id):
        @op
        def gen_op():
            yield AssetMaterialization(asset_key=AssetKey(["a"]))
            yield AssetMaterialization(asset_key=AssetKey(["c"]))
            yield AssetMaterialization(asset_key=AssetKey(["banana"]))
            yield AssetMaterialization(asset_key=AssetKey(["b", "x"]))
            yield AssetMaterialization(asset_key=AssetKey(["b", "y"]))
            yield AssetMaterialization(asset_key=AssetKey(["b", "z"]))
            yield Output(1)

        with instance_for_test() as created_instance:
            if not storage.has_instance:
                storage.register_instance(created_instance)

            events, _ = _synthesize_events(
                lambda: gen_op(), instance=created_instance, run_id=test_run_id
            )
            for event in events:
                storage.store_event(event)

            asset_keys = storage.get_asset_keys()
            assert len(asset_keys) == 6
            # should come out sorted
            assert [asset_key.to_string() for asset_key in asset_keys] == [
                '["a"]',
                '["b", "x"]',
                '["b", "y"]',
                '["b", "z"]',
                '["banana"]',
                '["c"]',
            ]

            # pagination fields
            asset_keys = storage.get_asset_keys(cursor='["b", "y"]', limit=1)
            assert len(asset_keys) == 1
            assert asset_keys[0].to_string() == '["b", "z"]'

            # prefix filter
            asset_keys = storage.get_asset_keys(prefix=["b"])
            assert len(asset_keys) == 3
            assert [asset_key.to_string() for asset_key in asset_keys] == [
                '["b", "x"]',
                '["b", "y"]',
                '["b", "z"]',
            ]

    def test_get_materialization_count_by_partition(self, storage, instance):
        a = AssetKey("no_materializations_asset")
        b = AssetKey("no_partitions_asset")
        c = AssetKey("two_partitions_asset")
        d = AssetKey("one_partition_asset")

        @op
        def materialize():
            yield AssetMaterialization(b)
            yield AssetMaterialization(c, partition="a")
            yield AssetObservation(a, partition="a")
            yield Output(None)

        @op
        def materialize_two():
            yield AssetMaterialization(d, partition="x")
            yield AssetMaterialization(c, partition="a")
            yield AssetMaterialization(c, partition="b")
            yield Output(None)

        def _fetch_counts(storage, after_cursor=None):
            return storage.get_materialization_count_by_partition([c, d], after_cursor=after_cursor)

        with instance_for_test() as created_instance:
            if not storage.has_instance:
                storage.register_instance(created_instance)

            run_id_1 = make_new_run_id()
            run_id_2 = make_new_run_id()
            run_id_3 = make_new_run_id()

            with create_and_delete_test_runs(instance, [run_id_1, run_id_2, run_id_3]):
                events_one, _ = _synthesize_events(
                    lambda: materialize(), instance=created_instance, run_id=run_id_1
                )
                for event in events_one:
                    storage.store_event(event)

                cursor_run1 = storage.get_event_records(
                    EventRecordsFilter(event_type=DagsterEventType.ASSET_MATERIALIZATION),
                    limit=1,
                    ascending=False,
                )[0].storage_id

                materialization_count_by_key = storage.get_materialization_count_by_partition(
                    [a, b, c]
                )

                assert materialization_count_by_key.get(a) == {}
                assert materialization_count_by_key.get(b) == {}
                assert materialization_count_by_key.get(c)["a"] == 1
                assert len(materialization_count_by_key.get(c)) == 1

                events_two, _ = _synthesize_events(
                    lambda: materialize_two(),
                    instance=created_instance,
                    run_id=run_id_2,
                )
                for event in events_two:
                    storage.store_event(event)

                materialization_count_by_key = storage.get_materialization_count_by_partition(
                    [a, b, c]
                )
                assert materialization_count_by_key.get(c)["a"] == 2
                assert materialization_count_by_key.get(c)["b"] == 1

                # after_cursor
                materialization_count_by_key_after_run1 = (
                    storage.get_materialization_count_by_partition(
                        [a, b, c], after_cursor=cursor_run1
                    )
                )
                assert materialization_count_by_key_after_run1.get(a) == {}
                assert materialization_count_by_key_after_run1.get(b) == {}
                assert materialization_count_by_key_after_run1.get(c)["a"] == 1
                assert materialization_count_by_key_after_run1.get(c)["b"] == 1
                assert len(materialization_count_by_key_after_run1.get(c)) == 2

                materialization_count_by_key_after_everything = (
                    storage.get_materialization_count_by_partition(
                        [a, b, c], after_cursor=9999999999
                    )
                )
                assert materialization_count_by_key_after_everything.get(a) == {}
                assert materialization_count_by_key_after_everything.get(b) == {}
                assert materialization_count_by_key_after_everything.get(c) == {}

                # wipe asset, make sure we respect that
                if self.can_wipe():
                    storage.wipe_asset(c)
                    materialization_count_by_partition = _fetch_counts(storage)
                    assert materialization_count_by_partition.get(c) == {}

                    # rematerialize wiped asset
                    events, _ = _synthesize_events(
                        lambda: materialize_two(),
                        instance=created_instance,
                        run_id=run_id_3,
                    )
                    for event in events:
                        storage.store_event(event)

                    materialization_count_by_partition = _fetch_counts(storage)
                    assert materialization_count_by_partition.get(c)["a"] == 1
                    assert materialization_count_by_partition.get(d)["x"] == 2

                    # make sure adding an after_cursor doesn't mess with the wiped events
                    assert (
                        _fetch_counts(storage, after_cursor=cursor_run1)
                        == materialization_count_by_partition
                    )
                    assert _fetch_counts(storage, after_cursor=9999999999) == {c: {}, d: {}}

    def test_get_latest_asset_partition_materialization_attempts_without_materializations(
        self, storage, instance
    ):
        def _assert_matches_not_including_event_id(result, expected):
            assert {
                partition: run_id for partition, (run_id, _event_id) in result.items()
            } == expected

        a = AssetKey(["a"])
        run_id_1 = make_new_run_id()
        run_id_2 = make_new_run_id()
        run_id_3 = make_new_run_id()
        run_id_4 = make_new_run_id()
        with create_and_delete_test_runs(instance, [run_id_1, run_id_2, run_id_3, run_id_4]):
            # no events
            _assert_matches_not_including_event_id(
                storage.get_latest_asset_partition_materialization_attempts_without_materializations(
                    a
                ),
                {},
            )

            storage.store_event(
                EventLogEntry(
                    error_info=None,
                    level="debug",
                    user_message="",
                    run_id=run_id_1,
                    timestamp=time.time(),
                    dagster_event=DagsterEvent(
                        DagsterEventType.ASSET_MATERIALIZATION_PLANNED.value,
                        "nonce",
                        event_specific_data=AssetMaterializationPlannedData(a, "foo"),
                    ),
                )
            )
            storage.store_event(
                EventLogEntry(
                    error_info=None,
                    level="debug",
                    user_message="",
                    run_id=run_id_2,
                    timestamp=time.time(),
                    dagster_event=DagsterEvent(
                        DagsterEventType.ASSET_MATERIALIZATION_PLANNED.value,
                        "nonce",
                        event_specific_data=AssetMaterializationPlannedData(a, "bar"),
                    ),
                )
            )

            # no materializations yet
            _assert_matches_not_including_event_id(
                storage.get_latest_asset_partition_materialization_attempts_without_materializations(
                    a
                ),
                {
                    "foo": run_id_1,
                    "bar": run_id_2,
                },
            )

            storage.store_event(
                EventLogEntry(
                    error_info=None,
                    level="debug",
                    user_message="",
                    run_id=run_id_1,
                    timestamp=time.time(),
                    dagster_event=DagsterEvent(
                        DagsterEventType.ASSET_MATERIALIZATION.value,
                        "nonce",
                        event_specific_data=StepMaterializationData(
                            AssetMaterialization(asset_key=a, partition="foo")
                        ),
                    ),
                )
            )

            # foo got materialized later in the same run
            _assert_matches_not_including_event_id(
                storage.get_latest_asset_partition_materialization_attempts_without_materializations(
                    a
                ),
                {"bar": run_id_2},
            )

            storage.store_event(
                EventLogEntry(
                    error_info=None,
                    level="debug",
                    user_message="",
                    run_id=run_id_3,
                    timestamp=time.time(),
                    dagster_event=DagsterEvent(
                        DagsterEventType.ASSET_MATERIALIZATION_PLANNED.value,
                        "nonce",
                        event_specific_data=AssetMaterializationPlannedData(a, "foo"),
                    ),
                )
            )

            # a new run has been started for foo
            _assert_matches_not_including_event_id(
                storage.get_latest_asset_partition_materialization_attempts_without_materializations(
                    a
                ),
                {
                    "foo": run_id_3,
                    "bar": run_id_2,
                },
            )

            storage.store_event(
                EventLogEntry(
                    error_info=None,
                    level="debug",
                    user_message="",
                    run_id=run_id_3,
                    timestamp=time.time(),
                    dagster_event=DagsterEvent(
                        DagsterEventType.ASSET_MATERIALIZATION_PLANNED.value,
                        "nonce",
                        event_specific_data=AssetMaterializationPlannedData(
                            AssetKey(["other"]), "foo"
                        ),
                    ),
                )
            )

            # other assets don't get included
            _assert_matches_not_including_event_id(
                storage.get_latest_asset_partition_materialization_attempts_without_materializations(
                    a
                ),
                {
                    "foo": run_id_3,
                    "bar": run_id_2,
                },
            )

            # other assets don't get included
            _assert_matches_not_including_event_id(
                storage.get_latest_asset_partition_materialization_attempts_without_materializations(
                    a
                ),
                {
                    "foo": run_id_3,
                    "bar": run_id_2,
                },
            )

            # wipe asset, make sure we respect that
            if self.can_wipe():
                storage.wipe_asset(a)
                _assert_matches_not_including_event_id(
                    storage.get_latest_asset_partition_materialization_attempts_without_materializations(
                        a
                    ),
                    {},
                )

                storage.store_event(
                    EventLogEntry(
                        error_info=None,
                        level="debug",
                        user_message="",
                        run_id=run_id_4,
                        timestamp=time.time(),
                        dagster_event=DagsterEvent(
                            DagsterEventType.ASSET_MATERIALIZATION_PLANNED.value,
                            "nonce",
                            event_specific_data=AssetMaterializationPlannedData(a, "bar"),
                        ),
                    )
                )

                # new materialization planned appears
                _assert_matches_not_including_event_id(
                    storage.get_latest_asset_partition_materialization_attempts_without_materializations(
                        a
                    ),
                    {
                        "bar": run_id_4,
                    },
                )

                storage.store_event(
                    EventLogEntry(
                        error_info=None,
                        level="debug",
                        user_message="",
                        run_id=run_id_4,
                        timestamp=time.time(),
                        dagster_event=DagsterEvent(
                            DagsterEventType.ASSET_MATERIALIZATION.value,
                            "nonce",
                            event_specific_data=StepMaterializationData(
                                AssetMaterialization(asset_key=a, partition="bar")
                            ),
                        ),
                    )
                )

                # and goes away
                _assert_matches_not_including_event_id(
                    storage.get_latest_asset_partition_materialization_attempts_without_materializations(
                        a
                    ),
                    {},
                )

    def test_get_latest_asset_partition_materialization_attempts_without_materializations_event_ids(
        self, storage, instance
    ):
        a = AssetKey(["a"])
        run_id_1 = make_new_run_id()
        run_id_2 = make_new_run_id()
        run_id_3 = make_new_run_id()
        with create_and_delete_test_runs(instance, [run_id_1, run_id_2, run_id_3]):
            storage.store_event(
                EventLogEntry(
                    error_info=None,
                    level="debug",
                    user_message="",
                    run_id=run_id_1,
                    timestamp=time.time(),
                    dagster_event=DagsterEvent(
                        DagsterEventType.ASSET_MATERIALIZATION_PLANNED.value,
                        "nonce",
                        event_specific_data=AssetMaterializationPlannedData(a, "foo"),
                    ),
                )
            )
            storage.store_event(
                EventLogEntry(
                    error_info=None,
                    level="debug",
                    user_message="",
                    run_id=run_id_2,
                    timestamp=time.time(),
                    dagster_event=DagsterEvent(
                        DagsterEventType.ASSET_MATERIALIZATION_PLANNED.value,
                        "nonce",
                        event_specific_data=AssetMaterializationPlannedData(a, "bar"),
                    ),
                )
            )
            records = storage.get_event_records(
                EventRecordsFilter(
                    event_type=DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
                    asset_key=a,
                )
            )
            assert len(records) == 2
            assert records[0].event_log_entry.dagster_event.event_specific_data.partition == "bar"
            assert records[1].event_log_entry.dagster_event.event_specific_data.partition == "foo"
            assert storage.get_latest_asset_partition_materialization_attempts_without_materializations(
                a
            ) == {
                "foo": (run_id_1, records[1].storage_id),
                "bar": (run_id_2, records[0].storage_id),
            }

            storage.store_event(
                EventLogEntry(
                    error_info=None,
                    level="debug",
                    user_message="",
                    run_id=run_id_3,
                    timestamp=time.time(),
                    dagster_event=DagsterEvent(
                        DagsterEventType.ASSET_MATERIALIZATION_PLANNED.value,
                        "nonce",
                        event_specific_data=AssetMaterializationPlannedData(a, "bar"),
                    ),
                )
            )

            assert storage.get_latest_asset_partition_materialization_attempts_without_materializations(
                a
            ) == {
                "foo": (run_id_1, records[1].storage_id),
                "bar": (run_id_3, records[0].storage_id + 1),
            }

    def test_get_observation(self, storage, test_run_id):
        a = AssetKey(["key_a"])

        @op
        def gen_op():
            yield AssetObservation(asset_key=a, metadata={"foo": "bar"})
            yield Output(1)

        with instance_for_test() as instance:
            if not storage.has_instance:
                storage.register_instance(instance)

            events_one, _ = _synthesize_events(
                lambda: gen_op(), instance=instance, run_id=test_run_id
            )
            for event in events_one:
                storage.store_event(event)

            records = storage.get_event_records(
                EventRecordsFilter(
                    event_type=DagsterEventType.ASSET_OBSERVATION,
                    asset_key=a,
                )
            )

            assert len(records) == 1

    def test_asset_key_exists_on_observation(self, storage, instance):
        key = AssetKey("hello")

        @op
        def my_op():
            yield AssetObservation(key)
            yield Output(5)

        run_id_1 = make_new_run_id()
        run_id_2 = make_new_run_id()
        with create_and_delete_test_runs(instance, [run_id_1, run_id_2]):
            with instance_for_test() as created_instance:
                if not storage.has_instance:
                    storage.register_instance(created_instance)

                events, _ = _synthesize_events(
                    lambda: my_op(), instance=created_instance, run_id=run_id_1
                )
                for event in events:
                    storage.store_event(event)

                assert [key] == storage.all_asset_keys()

                if self.can_wipe():
                    storage.wipe_asset(key)

                    assert len(storage.all_asset_keys()) == 0

                    events, _ = _synthesize_events(
                        lambda: my_op(), instance=created_instance, run_id=run_id_2
                    )
                    for event in events:
                        storage.store_event(event)

                    assert [key] == storage.all_asset_keys()

    def test_get_asset_records(self, storage, instance):
        @asset
        def my_asset():
            return 1

        @asset
        def second_asset(my_asset):  # pylint: disable=unused-argument
            return 2

        with instance_for_test() as created_instance:
            if not storage.has_instance:
                storage.register_instance(created_instance)

            my_asset_key = AssetKey("my_asset")
            # second_asset_key = AssetKey("second_asset")
            # storage.get_asset_records([my_asset_key, second_asset_key])

            assert len(storage.get_asset_records()) == 0

            run_id_1 = make_new_run_id()
            run_id_2 = make_new_run_id()
            with create_and_delete_test_runs(instance, [run_id_1, run_id_2]):
                asset_group = AssetGroup([my_asset, second_asset])
                result = _execute_job_and_store_events(
                    created_instance,
                    storage,
                    asset_group.build_job(name="one_asset_job", selection=["my_asset"]),
                    run_id=run_id_1,
                )
                records = storage.get_asset_records([my_asset_key])

                assert len(records) == 1
                asset_entry = records[0].asset_entry
                assert asset_entry.asset_key == my_asset_key
                materialize_event = [
                    event for event in result.all_events if event.is_step_materialization
                ][0]
                assert asset_entry.last_materialization.dagster_event == materialize_event
                assert asset_entry.last_run_id == result.run_id
                assert asset_entry.asset_details is None

                event_log_record = storage.get_event_records(
                    EventRecordsFilter(
                        event_type=DagsterEventType.ASSET_MATERIALIZATION,
                        asset_key=my_asset_key,
                    )
                )[0]
                assert asset_entry.last_materialization_record == event_log_record

                if self.can_wipe():
                    storage.wipe_asset(my_asset_key)

                    # confirm that last_run_id is None when asset is wiped
                    assert len(storage.get_asset_records([my_asset_key])) == 0

                    result = _execute_job_and_store_events(
                        created_instance,
                        storage,
                        asset_group.build_job(name="two_asset_job"),
                        run_id=run_id_2,
                    )
                    records = storage.get_asset_records([my_asset_key])
                    assert len(records) == 1
                    records = storage.get_asset_records([])  # should select no assets
                    assert len(records) == 0
                    records = storage.get_asset_records()  # should select all assets
                    assert len(records) == 2

                    records.sort(
                        key=lambda record: record.asset_entry.asset_key
                    )  # order by asset key
                    asset_entry = records[0].asset_entry
                    assert asset_entry.asset_key == my_asset_key
                    materialize_event = [
                        event for event in result.all_events if event.is_step_materialization
                    ][0]
                    assert asset_entry.last_materialization.dagster_event == materialize_event
                    assert asset_entry.last_run_id == result.run_id
                    assert isinstance(asset_entry.asset_details, AssetDetails)

    def test_asset_record_run_id_wiped(self, storage, instance):
        asset_key = AssetKey("foo")

        @op
        def materialize_asset():
            yield AssetMaterialization("foo")
            yield Output(5)

        @op
        def observe_asset():
            yield AssetObservation("foo")
            yield Output(5)

        run_id_1 = make_new_run_id()
        run_id_2 = make_new_run_id()
        run_id_3 = make_new_run_id()
        with create_and_delete_test_runs(instance, [run_id_1, run_id_2, run_id_3]):
            with instance_for_test() as created_instance:
                if not storage.has_instance:
                    storage.register_instance(created_instance)

                events, result = _synthesize_events(
                    lambda: observe_asset(), instance=created_instance, run_id=run_id_1
                )
                for event in events:
                    storage.store_event(event)
                asset_entry = storage.get_asset_records([asset_key])[0].asset_entry
                assert asset_entry.last_run_id is None

                events, result = _synthesize_events(
                    lambda: materialize_asset(),
                    instance=created_instance,
                    run_id=run_id_2,
                )
                for event in events:
                    storage.store_event(event)
                asset_entry = storage.get_asset_records([asset_key])[0].asset_entry
                assert asset_entry.last_run_id == result.run_id

                if self.can_wipe():
                    storage.wipe_asset(asset_key)
                    assert len(storage.get_asset_records([asset_key])) == 0

                    events, result = _synthesize_events(
                        lambda: observe_asset(),
                        instance=created_instance,
                        run_id=run_id_3,
                    )
                    for event in events:
                        storage.store_event(event)
                    asset_entry = storage.get_asset_records([asset_key])[0].asset_entry
                    assert asset_entry.last_run_id is None

    def test_last_run_id_updates_on_materialization_planned(self, storage, instance):
        @asset
        def never_materializes_asset():
            raise Exception("foo")

        run_id_1 = make_new_run_id()
        run_id_2 = make_new_run_id()
        with create_and_delete_test_runs(instance, [run_id_1, run_id_2]):
            with instance_for_test() as created_instance:
                if not storage.has_instance:
                    storage.register_instance(created_instance)

                asset_key = AssetKey("never_materializes_asset")
                never_materializes_job = build_assets_job(
                    "never_materializes_job", [never_materializes_asset]
                )

                result = _execute_job_and_store_events(
                    created_instance, storage, never_materializes_job, run_id=run_id_1
                )
                records = storage.get_asset_records([asset_key])

                assert len(records) == 1
                asset_record = records[0]
                assert result.run_id == asset_record.asset_entry.last_run_id

                if self.can_wipe():
                    storage.wipe_asset(asset_key)

                    # confirm that last_run_id is None when asset is wiped
                    assert len(storage.get_asset_records([asset_key])) == 0

                    result = _execute_job_and_store_events(
                        created_instance,
                        storage,
                        never_materializes_job,
                        run_id=run_id_2,
                    )
                    records = storage.get_asset_records([asset_key])
                    assert len(records) == 1
                    assert result.run_id == records[0].asset_entry.last_run_id

    def test_get_logs_for_all_runs_by_log_id_of_type(self, storage):
        if not storage.supports_event_consumer_queries():
            pytest.skip("storage does not support event consumer queries")

        @op
        def return_one(_):
            return 1

        def _ops():
            return_one()

        for _ in range(2):
            events, _ = _synthesize_events(_ops)
            for event in events:
                storage.store_event(event)

        assert _event_types(
            storage.get_logs_for_all_runs_by_log_id(
                dagster_event_type=DagsterEventType.RUN_SUCCESS,
            ).values()
        ) == [DagsterEventType.RUN_SUCCESS, DagsterEventType.RUN_SUCCESS]

        assert _event_types(
            storage.get_logs_for_all_runs_by_log_id(
                dagster_event_type=DagsterEventType.STEP_SUCCESS,
            ).values()
        ) == [DagsterEventType.STEP_SUCCESS, DagsterEventType.STEP_SUCCESS]

        assert _event_types(
            storage.get_logs_for_all_runs_by_log_id(
                dagster_event_type={
                    DagsterEventType.STEP_SUCCESS,
                    DagsterEventType.RUN_SUCCESS,
                },
            ).values()
        ) == [
            DagsterEventType.STEP_SUCCESS,
            DagsterEventType.RUN_SUCCESS,
            DagsterEventType.STEP_SUCCESS,
            DagsterEventType.RUN_SUCCESS,
        ]

    def test_get_logs_for_all_runs_by_log_id_cursor(self, storage):
        if not storage.supports_event_consumer_queries():
            pytest.skip("storage does not support event consumer queries")

        @op
        def return_one(_):
            return 1

        def _ops():
            return_one()

        for _ in range(2):
            events, _ = _synthesize_events(_ops)
            for event in events:
                storage.store_event(event)

        events_by_log_id = storage.get_logs_for_all_runs_by_log_id(
            dagster_event_type={
                DagsterEventType.STEP_SUCCESS,
                DagsterEventType.RUN_SUCCESS,
            },
        )

        assert _event_types(events_by_log_id.values()) == [
            DagsterEventType.STEP_SUCCESS,
            DagsterEventType.RUN_SUCCESS,
            DagsterEventType.STEP_SUCCESS,
            DagsterEventType.RUN_SUCCESS,
        ]

        after_cursor_events_by_log_id = storage.get_logs_for_all_runs_by_log_id(
            after_cursor=min(events_by_log_id.keys()),
            dagster_event_type={
                DagsterEventType.STEP_SUCCESS,
                DagsterEventType.RUN_SUCCESS,
            },
        )

        assert _event_types(after_cursor_events_by_log_id.values()) == [
            DagsterEventType.RUN_SUCCESS,
            DagsterEventType.STEP_SUCCESS,
            DagsterEventType.RUN_SUCCESS,
        ]

    def test_get_logs_for_all_runs_by_log_id_limit(self, storage):
        if not storage.supports_event_consumer_queries():
            pytest.skip("storage does not support event consumer queries")

        @op
        def return_one(_):
            return 1

        def _ops():
            return_one()

        for _ in range(2):
            events, _ = _synthesize_events(_ops)
            for event in events:
                storage.store_event(event)

        events_by_log_id = storage.get_logs_for_all_runs_by_log_id(
            dagster_event_type={
                DagsterEventType.STEP_SUCCESS,
                DagsterEventType.RUN_SUCCESS,
            },
            limit=3,
        )

        assert _event_types(events_by_log_id.values()) == [
            DagsterEventType.STEP_SUCCESS,
            DagsterEventType.RUN_SUCCESS,
            DagsterEventType.STEP_SUCCESS,
        ]

    def test_get_maximum_record_id(self, storage):
        if not storage.supports_event_consumer_queries():
            pytest.skip("storage does not support event consumer queries")

        storage.wipe()
        assert storage.get_maximum_record_id() is None

        storage.store_event(
            EventLogEntry(
                error_info=None,
                level="debug",
                user_message="",
                run_id="foo_run",
                timestamp=time.time(),
                dagster_event=DagsterEvent(
                    DagsterEventType.ENGINE_EVENT.value,
                    "nonce",
                    event_specific_data=EngineEventData.in_process(999),
                ),
            )
        )

        index = cast(int, storage.get_maximum_record_id())
        assert isinstance(index, int)

        for i in range(10):
            storage.store_event(
                EventLogEntry(
                    error_info=None,
                    level="debug",
                    user_message="",
                    run_id=f"foo_run_{i}",
                    timestamp=time.time(),
                    dagster_event=DagsterEvent(
                        DagsterEventType.ENGINE_EVENT.value,
                        "nonce",
                        event_specific_data=EngineEventData.in_process(999),
                    ),
                )
            )

        assert storage.get_maximum_record_id() == index + 10

    def test_get_materialization_tag(self, storage, instance):
        key = AssetKey("hello")

        @op
        def my_op():
            yield AssetMaterialization(
                asset_key=key,
                partition=MultiPartitionKey({"country": "US", "date": "2022-10-13"}),
                tags={
                    "dagster/partition/country": "US",
                    "dagster/partition/date": "2022-10-13",
                },
            )
            yield AssetMaterialization(
                asset_key=AssetKey("other_key"),
                partition=MultiPartitionKey({"country": "US", "date": "2022-10-13"}),
                tags={
                    "dagster/partition/country": "US",
                    "dagster/partition/date": "2022-10-13",
                },
            )
            yield Output(5)

        run_id = make_new_run_id()
        with create_and_delete_test_runs(instance, [run_id]):
            events, _ = _synthesize_events(lambda: my_op(), run_id)
            for event in events:
                storage.store_event(event)

            materializations = storage.get_event_records(
                EventRecordsFilter(DagsterEventType.ASSET_MATERIALIZATION)
            )
            assert len(materializations) == 2

            asset_event_tags = storage.get_event_tags_for_asset(key)
            assert asset_event_tags == [
                {"dagster/partition/country": "US", "dagster/partition/date": "2022-10-13"}
            ]

    def test_add_asset_event_tags(self, storage, instance):
        if not storage.supports_add_asset_event_tags():
            pytest.skip("storage does not support adding asset event tags")

        key = AssetKey("hello")

        @op
        def tags_op():
            yield AssetMaterialization(
                asset_key=key,
                partition=MultiPartitionKey({"country": "US", "date": "2022-10-13"}),
                tags={
                    "dagster/partition/country": "US",
                    "dagster/partition/date": "2022-10-13",
                },
            )
            yield Output(1)

        run_id = make_new_run_id()
        with create_and_delete_test_runs(instance, [run_id]):
            events, _ = _synthesize_events(lambda: tags_op(), run_id)
            for event in events:
                storage.store_event(event)

            materializations = storage.get_event_records(
                EventRecordsFilter(DagsterEventType.ASSET_MATERIALIZATION)
            )

            assert len(materializations) == 1
            mat_record = materializations[0]

            assert storage.get_event_tags_for_asset(key, filter_event_id=mat_record.storage_id) == [
                {
                    "dagster/partition/country": "US",
                    "dagster/partition/date": "2022-10-13",
                }
            ]

            storage.add_asset_event_tags(
                event_id=mat_record.storage_id,
                event_timestamp=mat_record.event_log_entry.timestamp,
                asset_key=mat_record.asset_key,
                new_tags={
                    "a": "apple",
                    "b": "boot",
                },
            )

            assert storage.get_event_tags_for_asset(key, filter_event_id=mat_record.storage_id) == [
                {
                    "a": "apple",
                    "b": "boot",
                    "dagster/partition/country": "US",
                    "dagster/partition/date": "2022-10-13",
                }
            ]

            storage.add_asset_event_tags(
                event_id=mat_record.storage_id,
                event_timestamp=mat_record.event_log_entry.timestamp,
                asset_key=mat_record.asset_key,
                new_tags={"a": "something_new"},
            )

            assert storage.get_event_tags_for_asset(key, filter_event_id=mat_record.storage_id) == [
                {
                    "a": "something_new",
                    "b": "boot",
                    "dagster/partition/country": "US",
                    "dagster/partition/date": "2022-10-13",
                }
            ]

    def test_add_asset_event_tags_initially_empty(self, storage, instance):
        if not storage.supports_add_asset_event_tags():
            pytest.skip("storage does not support adding asset event tags")
        key = AssetKey("hello")

        @op
        def tags_op():
            yield AssetMaterialization(asset_key=key)
            yield Output(1)

        run_id = make_new_run_id()
        with create_and_delete_test_runs(instance, [run_id]):
            events, _ = _synthesize_events(lambda: tags_op(), run_id)
            for event in events:
                storage.store_event(event)

            materializations = storage.get_event_records(
                EventRecordsFilter(DagsterEventType.ASSET_MATERIALIZATION)
            )

            assert len(materializations) == 1
            mat_record = materializations[0]

            assert (
                storage.get_event_tags_for_asset(key, filter_event_id=mat_record.storage_id) == []
            )

            storage.add_asset_event_tags(
                event_id=mat_record.storage_id,
                event_timestamp=mat_record.event_log_entry.timestamp,
                asset_key=mat_record.asset_key,
                new_tags={"a": "apple", "b": "boot"},
            )

            assert storage.get_event_tags_for_asset(key, filter_event_id=mat_record.storage_id) == [
                {"a": "apple", "b": "boot"}
            ]

    def test_materialization_tag_on_wipe(self, storage, instance):
        key = AssetKey("hello")

        @op
        def us_op():
            yield AssetMaterialization(
                asset_key=key,
                partition=MultiPartitionKey({"country": "US", "date": "2022-10-13"}),
                tags={
                    "dagster/partition/country": "US",
                    "dagster/partition/date": "2022-10-13",
                },
            )
            yield AssetMaterialization(
                asset_key=key,
                partition=MultiPartitionKey({"country": "Portugal", "date": "2022-10-13"}),
                tags={
                    "dagster/partition/country": "Portugal",
                    "dagster/partition/date": "2022-10-13",
                },
            )
            yield AssetMaterialization(
                asset_key=key,
                partition=MultiPartitionKey({"country": "US", "date": "2022-10-13"}),
                tags={
                    "dagster/partition/country": "US",
                    "dagster/partition/date": "2022-10-14",
                },
            )
            yield AssetMaterialization(
                asset_key=key,
                partition=MultiPartitionKey({"country": "US", "date": "2022-10-13"}),
                tags={
                    "dagster/partition/country": "US",
                    "dagster/partition/date": "2022-10-13",
                },
            )
            yield AssetMaterialization(
                asset_key=AssetKey("nonexistent_key"),
                partition=MultiPartitionKey({"country": "US", "date": "2022-10-13"}),
                tags={
                    "dagster/partition/country": "US",
                    "dagster/partition/date": "2022-10-13",
                },
            )
            yield Output(5)

        @op
        def brazil_op():
            yield AssetMaterialization(
                asset_key=key,
                partition=MultiPartitionKey({"country": "Brazil", "date": "2022-10-13"}),
                tags={
                    "dagster/partition/country": "Brazil",
                    "dagster/partition/date": "2022-10-13",
                },
            )
            yield Output(5)

        def _sort_by_country_then_date(tags):
            return sorted(
                tags,
                key=lambda tag: (tag["dagster/partition/country"]) + tag["dagster/partition/date"],
            )

        run_id = make_new_run_id()
        run_id_2 = make_new_run_id()
        with create_and_delete_test_runs(instance, [run_id, run_id_2]):
            events, _ = _synthesize_events(lambda: us_op(), run_id)
            for event in events:
                storage.store_event(event)

            asset_event_tags = _sort_by_country_then_date(
                storage.get_event_tags_for_asset(
                    asset_key=key, filter_tags={"dagster/partition/country": "US"}
                )
            )
            assert asset_event_tags == [
                {"dagster/partition/country": "US", "dagster/partition/date": "2022-10-13"},
                {"dagster/partition/country": "US", "dagster/partition/date": "2022-10-13"},
                {"dagster/partition/country": "US", "dagster/partition/date": "2022-10-14"},
            ]
            asset_event_tags = _sort_by_country_then_date(
                storage.get_event_tags_for_asset(
                    asset_key=key, filter_tags={"dagster/partition/date": "2022-10-13"}
                )
            )
            assert asset_event_tags == [
                {"dagster/partition/country": "Portugal", "dagster/partition/date": "2022-10-13"},
                {"dagster/partition/country": "US", "dagster/partition/date": "2022-10-13"},
                {"dagster/partition/country": "US", "dagster/partition/date": "2022-10-13"},
            ]
            asset_event_tags = _sort_by_country_then_date(
                storage.get_event_tags_for_asset(
                    asset_key=key,
                    filter_tags={
                        "dagster/partition/date": "2022-10-13",
                        "dagster/partition/country": "US",
                    },
                )
            )
            assert asset_event_tags == [
                {"dagster/partition/country": "US", "dagster/partition/date": "2022-10-13"},
                {"dagster/partition/country": "US", "dagster/partition/date": "2022-10-13"},
            ]
            if self.can_wipe():
                storage.wipe_asset(key)
                asset_event_tags = storage.get_event_tags_for_asset(
                    asset_key=key,
                )
                assert asset_event_tags == []

                events, _ = _synthesize_events(lambda: brazil_op(), run_id_2)
                for event in events:
                    storage.store_event(event)

                asset_event_tags = storage.get_event_tags_for_asset(
                    asset_key=key,
                    filter_tags={
                        "dagster/partition/date": "2022-10-13",
                        "dagster/partition/country": "Brazil",
                    },
                )
                assert asset_event_tags == [
                    {"dagster/partition/country": "Brazil", "dagster/partition/date": "2022-10-13"}
                ]

    def test_event_record_filter_tags(self, storage, instance):
        key = AssetKey("hello")

        @op
        def my_op():
            yield AssetObservation(
                asset_key=key, metadata={"foo": "bar"}
            )  # should not show up in any queries
            yield AssetMaterialization(
                asset_key=key,
                partition=MultiPartitionKey({"country": "US", "date": "2022-10-13"}),
                tags={
                    "dagster/partition/country": "US",
                    "dagster/partition/date": "2022-10-13",
                },
            )
            yield AssetMaterialization(
                asset_key=key,
                partition=MultiPartitionKey({"country": "US", "date": "2022-10-13"}),
                tags={
                    "dagster/partition/country": "US",
                    "dagster/partition/date": "2022-10-13",
                },
            )
            yield AssetMaterialization(
                asset_key=key,
                partition=MultiPartitionKey({"country": "Canada", "date": "2022-10-13"}),
                tags={
                    "dagster/partition/country": "Canada",
                    "dagster/partition/date": "2022-10-13",
                },
            )
            yield AssetMaterialization(
                asset_key=key,
                partition=MultiPartitionKey({"country": "Mexico", "date": "2022-10-14"}),
                tags={
                    "dagster/partition/country": "Mexico",
                    "dagster/partition/date": "2022-10-14",
                },
            )
            yield Output(5)

        run_id = make_new_run_id()
        with create_and_delete_test_runs(instance, [run_id]):
            events, _ = _synthesize_events(lambda: my_op(), run_id)
            for event in events:
                storage.store_event(event)

            materializations = storage.get_event_records(
                EventRecordsFilter(DagsterEventType.ASSET_MATERIALIZATION)
            )
            assert len(materializations) == 4

            materializations = storage.get_event_records(
                EventRecordsFilter(
                    DagsterEventType.ASSET_MATERIALIZATION,
                    asset_key=key,
                    tags={
                        "dagster/partition/date": "2022-10-13",
                        "dagster/partition/country": "US",
                    },
                )
            )
            assert len(materializations) == 2
            for record in materializations:
                materialization = (
                    record.event_log_entry.dagster_event.step_materialization_data.materialization
                )

                assert isinstance(materialization.partition, MultiPartitionKey)
                assert materialization.partition == MultiPartitionKey(
                    {"country": "US", "date": "2022-10-13"}
                )
                assert materialization.partition.keys_by_dimension == {
                    "country": "US",
                    "date": "2022-10-13",
                }
                assert materialization.tags == {
                    "dagster/partition/country": "US",
                    "dagster/partition/date": "2022-10-13",
                }

            materializations = storage.get_event_records(
                EventRecordsFilter(
                    DagsterEventType.ASSET_MATERIALIZATION,
                    asset_key=key,
                    tags={"nonexistent": "tag"},
                )
            )
            assert len(materializations) == 0

            materializations = storage.get_event_records(
                EventRecordsFilter(
                    DagsterEventType.ASSET_MATERIALIZATION,
                    asset_key=key,
                    tags={"dagster/partition/date": "2022-10-13"},
                )
            )
            assert len(materializations) == 3
            for record in materializations:
                materialization = (
                    record.event_log_entry.dagster_event.step_materialization_data.materialization
                )
                date_dimension = [
                    dimension
                    for dimension in materialization.partition.dimension_keys
                    if dimension.dimension_name == "date"
                ][0]
                assert date_dimension.partition_key == "2022-10-13"

    def test_event_records_filter_tags_requires_asset_key(self, storage):
        with pytest.raises(Exception, match="Asset key must be set in event records"):
            storage.get_event_records(
                EventRecordsFilter(
                    DagsterEventType.ASSET_MATERIALIZATION,
                    tags={"dagster/partition/date": "2022-10-13"},
                )
            )

    def test_multi_partitions_partition_deserialization(self, storage, instance):
        key = AssetKey("hello")

        @op
        def my_op():
            yield AssetMaterialization(
                asset_key=key,
                partition=MultiPartitionKey({"country": "US", "date": "2022-10-13"}),
            )
            yield AssetMaterialization(
                asset_key=key,
                partition=MultiPartitionKey({"country": "US", "date": "2022-10-13"}),
            )
            yield AssetMaterialization(
                asset_key=key,
                partition=MultiPartitionKey({"country": "Canada", "date": "2022-10-13"}),
            )
            yield AssetMaterialization(
                asset_key=key,
                partition=MultiPartitionKey({"country": "Mexico", "date": "2022-10-14"}),
            )
            yield Output(5)

        with instance_for_test() as created_instance:
            if not storage.has_instance:
                storage.register_instance(created_instance)

            run_id_1 = make_new_run_id()

            with create_and_delete_test_runs(instance, [run_id_1]):
                events_one, _ = _synthesize_events(
                    lambda: my_op(), instance=created_instance, run_id=run_id_1
                )
                for event in events_one:
                    storage.store_event(event)

            materialization_counts = created_instance.get_materialization_count_by_partition([key])
            assert (
                materialization_counts[key][
                    MultiPartitionKey({"country": "US", "date": "2022-10-13"})
                ]
                == 2
            )
            assert (
                materialization_counts[key][
                    MultiPartitionKey({"country": "Mexico", "date": "2022-10-14"})
                ]
                == 1
            )
            assert (
                materialization_counts[key][
                    MultiPartitionKey({"country": "Canada", "date": "2022-10-13"})
                ]
                == 1
            )

    def test_store_and_wipe_cached_status(self, storage, instance):
        asset_key = AssetKey("yay")

        @op
        def yields_materialization():
            yield AssetMaterialization(asset_key=asset_key)
            yield Output(1)

        run_id_1, run_id_2 = make_new_run_id(), make_new_run_id()
        with create_and_delete_test_runs(instance, [run_id_1, run_id_2]):
            events, _ = _synthesize_events(
                lambda: yields_materialization(),
                run_id=run_id_1,
            )
            for event in events:
                storage.store_event(event)

            assert _get_cached_status_for_asset(storage, asset_key) is None

            cache_value = AssetStatusCacheValue(
                latest_storage_id=1,
                partitions_def_id="foo",
                serialized_materialized_partition_subset="bar",
                serialized_failed_partition_subset="baz",
                earliest_in_progress_materialization_event_id=42,
            )
            storage.update_asset_cached_status_data(asset_key=asset_key, cache_values=cache_value)

            assert _get_cached_status_for_asset(storage, asset_key) == cache_value

            cache_value = AssetStatusCacheValue(
                latest_storage_id=1,
                partitions_def_id=None,
                serialized_materialized_partition_subset=None,
            )
            storage.update_asset_cached_status_data(asset_key=asset_key, cache_values=cache_value)

            assert _get_cached_status_for_asset(storage, asset_key) == cache_value

            if self.can_wipe():
                storage.wipe_asset(asset_key)
                assert storage.get_asset_records() == []

                events, _ = _synthesize_events(
                    lambda: yields_materialization(),
                    run_id=run_id_2,
                )
                for event in events:
                    storage.store_event(event)

                assert _get_cached_status_for_asset(storage, asset_key) is None

    def test_add_dynamic_partitions(self, storage):
        assert storage

        assert storage.get_dynamic_partitions("foo") == []

        storage.add_dynamic_partitions(
            partitions_def_name="foo", partition_keys=["foo", "bar", "baz"]
        )
        partitions = storage.get_dynamic_partitions("foo")
        assert len(partitions) == 3
        assert partitions == ["foo", "bar", "baz"]

        # Test for idempotency
        storage.add_dynamic_partitions(partitions_def_name="foo", partition_keys=["foo"])
        partitions = storage.get_dynamic_partitions("foo")
        assert len(partitions) == 3
        assert partitions == ["foo", "bar", "baz"]

        storage.add_dynamic_partitions(partitions_def_name="foo", partition_keys=["foo", "qux"])
        partitions = storage.get_dynamic_partitions("foo")
        assert len(partitions) == 4
        assert partitions == ["foo", "bar", "baz", "qux"]

        assert set(storage.get_dynamic_partitions("baz")) == set()

    def test_delete_dynamic_partitions(self, storage):
        assert storage

        assert storage.get_dynamic_partitions("foo") == []

        storage.add_dynamic_partitions(
            partitions_def_name="foo", partition_keys=["foo", "bar", "baz"]
        )
        assert set(storage.get_dynamic_partitions("foo")) == {"foo", "bar", "baz"}

        storage.delete_dynamic_partition(partitions_def_name="foo", partition_key="foo")
        assert set(storage.get_dynamic_partitions("foo")) == {"bar", "baz"}

        # Test for idempotency
        storage.delete_dynamic_partition(partitions_def_name="foo", partition_key="foo")
        assert set(storage.get_dynamic_partitions("foo")) == {"bar", "baz"}

        storage.delete_dynamic_partition(partitions_def_name="bar", partition_key="foo")
        assert set(storage.get_dynamic_partitions("baz")) == set()

    def test_has_dynamic_partition(self, storage):
        assert storage
        assert storage.get_dynamic_partitions("foo") == []
        assert (
            storage.has_dynamic_partition(partitions_def_name="foo", partition_key="foo") is False
        )

        storage.add_dynamic_partitions(
            partitions_def_name="foo", partition_keys=["foo", "bar", "baz"]
        )
        assert storage.has_dynamic_partition(partitions_def_name="foo", partition_key="foo")
        assert not storage.has_dynamic_partition(partitions_def_name="foo", partition_key="qux")
        assert not storage.has_dynamic_partition(partitions_def_name="bar", partition_key="foo")
