import datetime
import logging  # noqa: F401; used by mock in string form
import random
import re
import string
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack, contextmanager
from typing import List, Optional, Sequence, Tuple, cast

import mock
import pendulum
import pytest
import sqlalchemy as db
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
from dagster._check import CheckError
from dagster._core.assets import AssetDetails
from dagster._core.definitions import ExpectationResult
from dagster._core.definitions.asset_check_evaluation import (
    AssetCheckEvaluation,
    AssetCheckEvaluationPlanned,
    AssetCheckEvaluationTargetMaterializationData,
)
from dagster._core.definitions.asset_check_spec import AssetCheckKey, AssetCheckSeverity
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.dependency import NodeHandle
from dagster._core.definitions.job_base import InMemoryJob
from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionKey
from dagster._core.definitions.partition import PartitionKeyRange
from dagster._core.definitions.time_window_partitions import (
    DailyPartitionsDefinition,
    PartitionKeysTimeWindowPartitionsSubset,
)
from dagster._core.definitions.unresolved_asset_job_definition import define_asset_job
from dagster._core.errors import DagsterInvalidInvocationError, DagsterInvariantViolationError
from dagster._core.event_api import EventLogCursor, EventRecordsResult, RunStatusChangeRecordsFilter
from dagster._core.events import (
    EVENT_TYPE_TO_PIPELINE_RUN_STATUS,
    AssetMaterializationPlannedData,
    AssetObservationData,
    DagsterEvent,
    DagsterEventType,
    EngineEventData,
    StepExpectationResultData,
    StepMaterializationData,
)
from dagster._core.events.log import EventLogEntry, construct_event_logger
from dagster._core.execution.api import execute_run
from dagster._core.execution.job_execution_result import JobExecutionResult
from dagster._core.execution.plan.handle import StepHandle
from dagster._core.execution.plan.objects import StepFailureData, StepSuccessData
from dagster._core.execution.stats import StepEventStatus
from dagster._core.host_representation.external_data import (
    external_partitions_definition_from_def,
)
from dagster._core.host_representation.origin import (
    ExternalJobOrigin,
    ExternalRepositoryOrigin,
    InProcessCodeLocationOrigin,
)
from dagster._core.instance import RUNLESS_JOB_NAME, RUNLESS_RUN_ID
from dagster._core.storage.asset_check_execution_record import (
    AssetCheckExecutionRecordStatus,
)
from dagster._core.storage.event_log import InMemoryEventLogStorage, SqlEventLogStorage
from dagster._core.storage.event_log.base import EventLogStorage
from dagster._core.storage.event_log.migration import (
    EVENT_LOG_DATA_MIGRATIONS,
    migrate_asset_key_data,
)
from dagster._core.storage.event_log.schema import SqlEventLogStorageTable
from dagster._core.storage.event_log.sqlite.sqlite_event_log import SqliteEventLogStorage
from dagster._core.storage.partition_status_cache import AssetStatusCacheValue
from dagster._core.storage.sqlalchemy_compat import db_select
from dagster._core.test_utils import create_run_for_test, instance_for_test
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.utils import make_new_run_id
from dagster._loggers import colored_console_logger
from dagster._serdes.serdes import deserialize_value
from dagster._utils import datetime_as_float
from dagster._utils.concurrency import ConcurrencySlotStatus

TEST_TIMEOUT = 5

# py36 & 37 list.append not hashable


@contextmanager
def create_and_delete_test_runs(instance: DagsterInstance, run_ids: Sequence[str]):
    check.opt_inst_param(instance, "instance", DagsterInstance)
    check.sequence_param(run_ids, "run_ids", of_type=str)
    if instance:
        for run_id in run_ids:
            create_run_for_test(
                instance,
                run_id=run_id,
                external_job_origin=ExternalJobOrigin(
                    ExternalRepositoryOrigin(
                        InProcessCodeLocationOrigin(
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


def _event_record(run_id, op_name, timestamp, event_type, event_specific_data=None):
    job_name = "pipeline_name"
    node_handle = NodeHandle(op_name, None)
    step_handle = StepHandle(node_handle)
    return EventLogEntry(
        error_info=None,
        user_message="",
        level="debug",
        run_id=run_id,
        timestamp=timestamp,
        step_key=step_handle.to_key(),
        job_name=job_name,
        dagster_event=DagsterEvent(
            event_type.value,
            job_name,
            node_handle=node_handle,
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
) -> Tuple[List[EventLogEntry], JobExecutionResult]:
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

        dagster_run = instance.create_run_for_job(a_job, run_id=run_id, run_config=run_config)
        result = execute_run(InMemoryJob(a_job), dagster_run, instance)

        if check_success:
            assert result.success

    assert result

    return events, result


def _store_materialization_events(storage, ops_fn, instance, run_id):
    events, _ = _synthesize_events(lambda: ops_fn(), instance=instance, run_id=run_id)
    for event in events:
        storage.store_event(event)
    last_materialization = storage.get_event_records(
        EventRecordsFilter(event_type=DagsterEventType.ASSET_MATERIALIZATION),
        limit=1,
        ascending=False,
    )[0]
    return last_materialization.storage_id + 1


def _fetch_all_events(configured_storage, run_id=None) -> Sequence[Tuple[str]]:
    with configured_storage.run_connection(run_id=run_id) as conn:
        res = conn.execute(db.text("SELECT event from event_logs"))
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


def one_asset_op():
    asset_op_one()


def two_asset_ops():
    asset_op_one()
    asset_op_two()


@op
def return_one_op(_):
    return 1


def return_one_op_func():
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
        def event_log_storage(self):
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
    def instance(self, request) -> Optional[DagsterInstance]:
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

    def has_asset_partitions_table(self) -> bool:
        return False

    def can_set_concurrency_defaults(self):
        return False

    def set_default_op_concurrency(self, instance, storage, limit):
        pass

    def test_event_log_storage_store_events_and_wipe(self, test_run_id, storage: EventLogStorage):
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

    def test_event_log_storage_store_with_multiple_runs(
        self,
        instance: DagsterInstance,
        storage: EventLogStorage,
    ):
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

    # .watch() is async, there's a small chance they don't run before the asserts
    @pytest.mark.flaky(reruns=1)
    def test_event_log_storage_watch(
        self,
        test_run_id: str,
        storage: EventLogStorage,
    ):
        if not self.can_watch():
            pytest.skip("storage cannot watch runs")

        watched = []
        watcher = lambda x, y: watched.append(x)

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

        first_two_records = storage.get_records_for_run(test_run_id, limit=2)
        assert len(first_two_records.records) == 2

        last_two_records = storage.get_records_for_run(test_run_id, limit=2, ascending=False)
        assert len(last_two_records.records) == 2

        assert storage.get_logs_for_run(test_run_id, limit=2, ascending=True) == [
            r.event_log_entry for r in first_two_records.records
        ]

        assert storage.get_logs_for_run(test_run_id, limit=2, ascending=False) == [
            r.event_log_entry for r in last_two_records.records
        ]

        assert storage.get_records_for_run(
            test_run_id, limit=2, cursor=first_two_records.cursor
        ).records == list(reversed(last_two_records.records))
        assert storage.get_records_for_run(
            test_run_id, limit=2, cursor=last_two_records.cursor, ascending=False
        ).records == list(reversed(first_two_records.records))

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

    def test_event_log_storage_pagination(
        self,
        test_run_id: str,
        instance: DagsterInstance,
        storage: EventLogStorage,
    ):
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

    def test_event_log_delete(
        self,
        test_run_id: str,
        storage: EventLogStorage,
    ):
        assert len(storage.get_logs_for_run(test_run_id)) == 0
        storage.store_event(create_test_event_log_record(str(0), test_run_id))
        assert len(storage.get_logs_for_run(test_run_id)) == 1
        assert storage.get_stats_for_run(test_run_id)
        storage.delete_events(test_run_id)
        assert len(storage.get_logs_for_run(test_run_id)) == 0

    def test_event_log_get_stats_without_start_and_success(
        self,
        test_run_id: str,
        storage: EventLogStorage,
    ):
        # When an event log doesn't have a PIPELINE_START or PIPELINE_SUCCESS | PIPELINE_FAILURE event,
        # we want to ensure storage.get_stats_for_run(...) doesn't throw an error.
        assert len(storage.get_logs_for_run(test_run_id)) == 0
        assert storage.get_stats_for_run(test_run_id)

    def test_event_log_get_stats_for_run(
        self,
        test_run_id: str,
        storage: EventLogStorage,
    ):
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
        stats = storage.get_stats_for_run(test_run_id)
        assert stats.enqueued_time
        assert math.isclose(stats.enqueued_time, enqueued_time)
        assert stats.launch_time
        assert math.isclose(stats.launch_time, launched_time)
        assert stats.start_time
        assert math.isclose(stats.start_time, start_time)

    def test_event_log_step_stats(
        self,
        test_run_id: str,
        storage: EventLogStorage,
    ):
        # When an event log doesn't have a PIPELINE_START or PIPELINE_SUCCESS | PIPELINE_FAILURE event,
        # we want to ensure storage.get_stats_for_run(...) doesn't throw an error.

        for record in _stats_records(run_id=test_run_id):
            storage.store_event(record)

        step_stats = storage.get_step_stats_for_run(test_run_id)
        assert len(step_stats) == 4

        a_stats = next(stats for stats in step_stats if stats.step_key == "A")
        assert a_stats.step_key == "A"
        assert a_stats.status
        assert a_stats.status.value == "SUCCESS"
        assert a_stats.end_time
        assert a_stats.start_time
        assert a_stats.end_time - a_stats.start_time == 100
        assert len(a_stats.attempts_list) == 1

        b_stats = next(stats for stats in step_stats if stats.step_key == "B")
        assert b_stats.step_key == "B"
        assert b_stats.status
        assert b_stats.status.value == "FAILURE"
        assert b_stats.end_time
        assert b_stats.start_time
        assert b_stats.end_time - b_stats.start_time == 50
        assert len(b_stats.attempts_list) == 1

        c_stats = next(stats for stats in step_stats if stats.step_key == "C")
        assert c_stats.step_key == "C"
        assert c_stats.status
        assert c_stats.status.value == "SKIPPED"
        assert c_stats.end_time
        assert c_stats.start_time
        assert c_stats.end_time - c_stats.start_time == 25
        assert len(c_stats.attempts_list) == 1

        d_stats = next(stats for stats in step_stats if stats.step_key == "D")
        assert d_stats.step_key == "D"
        assert d_stats.status
        assert d_stats.status.value == "SUCCESS"
        assert d_stats.end_time
        assert d_stats.start_time
        assert d_stats.end_time - d_stats.start_time == 150
        assert len(d_stats.materialization_events) == 3
        assert len(d_stats.expectation_results) == 2
        assert len(c_stats.attempts_list) == 1

    def test_secondary_index(self, storage: EventLogStorage):
        if not isinstance(storage, SqlEventLogStorage) or isinstance(
            storage, InMemoryEventLogStorage
        ):
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

    def test_basic_event_store(
        self,
        test_run_id: str,
        storage: EventLogStorage,
    ):
        from collections import Counter as CollectionsCounter

        if not isinstance(storage, SqlEventLogStorage):
            pytest.skip("This test is for SQL-backed Event Log behavior")

        events, _result = _synthesize_events(return_one_op_func, run_id=test_run_id)

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
        events, result = _synthesize_events(return_one_op_func, run_id=test_run_id)

        for event in events:
            storage.store_event(event)
        out_events = storage.get_logs_for_run(result.run_id)

        assert _event_types(out_events) == _event_types(events)

    def test_get_logs_for_run_cursor_limit(self, test_run_id, storage):
        events, result = _synthesize_events(return_one_op_func, run_id=test_run_id)

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
        events, result = _synthesize_events(return_one_op_func, run_id=test_run_id)

        for event in events:
            storage.store_event(event)

        out_events = storage.get_logs_for_run(result.run_id)

        assert _event_types(out_events) == _event_types(events)

        if self.can_wipe():
            storage.wipe()

            assert storage.get_logs_for_run(result.run_id) == []

    def test_delete_sql_backed_event_log(self, test_run_id, storage):
        events, result = _synthesize_events(return_one_op_func, run_id=test_run_id)

        for event in events:
            storage.store_event(event)

        out_events = storage.get_logs_for_run(result.run_id)

        assert _event_types(out_events) == _event_types(events)

        storage.delete_events(result.run_id)

        assert storage.get_logs_for_run(result.run_id) == []

    def test_get_logs_for_run_of_type(self, test_run_id, storage):
        events, result = _synthesize_events(return_one_op_func, run_id=test_run_id)

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
        events, result = _synthesize_events(return_one_op_func, run_id=test_run_id)

        for event in events:
            storage.store_event(event)

        assert _event_types(storage.get_logs_for_run(result.run_id, cursor=-1)) == _event_types(
            events
        )

    def test_basic_get_logs_for_run_multiple_runs(self, instance, storage):
        events_one, result_one = _synthesize_events(return_one_op_func)
        events_two, result_two = _synthesize_events(return_one_op_func)

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
        events_one, result_one = _synthesize_events(return_one_op_func)
        events_two, result_two = _synthesize_events(return_one_op_func)

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

    # .watch() is async, there's a small chance they don't run before the asserts
    @pytest.mark.flaky(reruns=1)
    def test_event_watcher_single_run_event(self, storage, test_run_id):
        if not self.can_watch():
            pytest.skip("storage cannot watch runs")

        event_list = []

        storage.watch(test_run_id, None, lambda x, _y: event_list.append(x))

        events, _ = _synthesize_events(return_one_op_func, run_id=test_run_id)
        for event in events:
            storage.store_event(event)

        start = time.time()
        while len(event_list) < len(events) and time.time() - start < TEST_TIMEOUT:
            time.sleep(0.01)

        assert len(event_list) == len(events)
        assert all([isinstance(event, EventLogEntry) for event in event_list])

    # .watch() is async, there's a small chance they don't run before the asserts
    @pytest.mark.flaky(reruns=1)
    def test_event_watcher_filter_run_event(self, instance, storage):
        if not self.can_watch():
            pytest.skip("storage cannot watch runs")

        run_id_one = make_new_run_id()
        run_id_two = make_new_run_id()

        with create_and_delete_test_runs(instance, [run_id_one, run_id_two]):
            # only watch one of the runs
            event_list = []
            storage.watch(run_id_two, None, lambda x, _y: event_list.append(x))

            events_one, _result_one = _synthesize_events(return_one_op_func, run_id=run_id_one)
            for event in events_one:
                storage.store_event(event)

            events_two, _result_two = _synthesize_events(return_one_op_func, run_id=run_id_two)
            for event in events_two:
                storage.store_event(event)

            start = time.time()
            while len(event_list) < len(events_two) and time.time() - start < TEST_TIMEOUT:
                time.sleep(0.01)

            assert len(event_list) == len(events_two)
            assert all([isinstance(event, EventLogEntry) for event in event_list])

    # .watch() is async, there's a small chance they don't run before the asserts
    @pytest.mark.flaky(reruns=1)
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

            events_one, _result_one = _synthesize_events(return_one_op_func, run_id=run_id_one)
            for event in events_one:
                storage.store_event(event)

            events_two, _result_two = _synthesize_events(return_one_op_func, run_id=run_id_two)
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

            # legacy API
            records = storage.get_event_records(
                EventRecordsFilter(
                    event_type=DagsterEventType.ASSET_MATERIALIZATION,
                    asset_key=asset_key,
                )
            )
            assert len(records) == 1
            record = records[0]
            assert isinstance(record, EventLogRecord)
            assert record.event_log_entry.dagster_event
            assert record.event_log_entry.dagster_event.asset_key == asset_key

            # new API
            result = storage.fetch_materializations(asset_key, limit=100)
            assert isinstance(result, EventRecordsResult)
            assert len(result.records) == 1
            record = result.records[0]
            assert record.event_log_entry.dagster_event
            assert record.event_log_entry.dagster_event.asset_key == asset_key
            assert result.cursor == EventLogCursor.from_storage_id(record.storage_id).to_string()

    def test_asset_materialization_null_key_fails(self):
        with pytest.raises(check.CheckError):
            AssetMaterialization(asset_key=None)

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

    def test_get_run_status_change_events(self, storage, instance):
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

            all_success_events = storage.fetch_run_status_changes(
                DagsterEventType.RUN_SUCCESS, limit=100
            ).records
            assert len(all_success_events) == 3
            assert all_success_events[0].storage_id > all_success_events[2].storage_id
            assert (
                len(
                    storage.fetch_run_status_changes(
                        DagsterEventType.RUN_SUCCESS,
                        cursor=str(
                            EventLogCursor.from_storage_id(all_success_events[1].storage_id)
                        ),
                        limit=100,
                    ).records
                )
                == 1
            )
            assert (
                len(
                    storage.fetch_run_status_changes(
                        RunStatusChangeRecordsFilter(
                            DagsterEventType.RUN_SUCCESS,
                            after_storage_id=all_success_events[1].storage_id,
                        ),
                        limit=100,
                    ).records
                )
            ) == 1
            assert [
                i.storage_id
                for i in storage.fetch_run_status_changes(
                    DagsterEventType.RUN_SUCCESS,
                    ascending=True,
                    limit=2,
                ).records
            ] == [record.storage_id for record in all_success_events[::-1][:2]]

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
                InMemoryJob(a_job),
                instance.create_run_for_job(
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
                InMemoryJob(a_job),
                instance.create_run_for_job(
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
                InMemoryJob(a_job),
                instance.create_run_for_job(
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

            # check that events were double-written to the index shard
            with storage.index_connection() as conn:
                run_status_change_events = conn.execute(
                    db_select([SqlEventLogStorageTable.c.id]).where(
                        SqlEventLogStorageTable.c.dagster_event_type.in_(
                            [
                                event_type.value
                                for event_type in EVENT_TYPE_TO_PIPELINE_RUN_STATUS.keys()
                            ]
                        )
                    )
                ).fetchall()
                assert len(run_status_change_events) == 6

    # .watch() is async, there's a small chance they don't run before the asserts
    @pytest.mark.flaky(reruns=1)
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

        err_events, _ = _synthesize_events(return_one_op_func, run_id=err_run_id)
        safe_events, _ = _synthesize_events(return_one_op_func, run_id=safe_run_id)

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

        err_events, _ = _synthesize_events(return_one_op_func, run_id=err_run_id)
        safe_events, _ = _synthesize_events(return_one_op_func, run_id=safe_run_id)

        event_list = []

        # Direct end_watch emulates behavior of clean up on exception downstream
        # of the subscription in the webserver.
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
            run = instance.create_run_for_job(a_job, run_id=run_id)

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
                lambda: one_asset_op(), instance=created_instance
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
                lambda: one_asset_op(), instance=created_instance
            )
            events_two, result_2 = _synthesize_events(
                lambda: two_asset_ops(), instance=created_instance
            )

            with create_and_delete_test_runs(instance, [result_1.run_id, result_2.run_id]):
                for event in events_one + events_two:
                    storage.store_event(event)

                assert storage.has_asset_key(AssetKey(["path", "to", "asset_3"]))
                assert not storage.has_asset_key(AssetKey(["path", "to", "bogus", "asset"]))

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
                lambda: one_asset_op(), run_id=one_run_id, instance=created_instance
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

                log_count = len(storage.get_logs_for_run(one_run_id))
                if self.can_wipe():
                    for asset_key in asset_keys:
                        storage.wipe_asset(asset_key)

                    asset_keys = storage.all_asset_keys()
                    assert len(asset_keys) == 0
                    assert not storage.has_asset_key(AssetKey("asset_1"))
                    assert log_count == len(storage.get_logs_for_run(one_run_id))

                    one_run_id = "one_run_id_2"
                    events_one, _ = _synthesize_events(
                        lambda: one_asset_op(),
                        run_id=one_run_id,
                        instance=created_instance,
                    )
                    with create_and_delete_test_runs(instance, [one_run_id]):
                        for event in events_one:
                            storage.store_event(event)

                        asset_keys = storage.all_asset_keys()
                        assert len(asset_keys) == 1
                        assert storage.has_asset_key(AssetKey("asset_1"))

    def test_asset_secondary_index(self, storage, instance):
        with instance_for_test() as created_instance:
            if not storage.has_instance:
                storage.register_instance(created_instance)

            events_one, result = _synthesize_events(
                lambda: one_asset_op(), instance=created_instance
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
                    # we now no longer keep the asset catalog keys in sync with the presence of
                    # asset events in the event log
                    # assert len(asset_keys) == 1

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

    def test_get_materialized_partitions(self, storage, instance):
        a = AssetKey("no_materializations_asset")
        b = AssetKey("no_partitions_asset")
        c = AssetKey("two_partitions_asset")
        d = AssetKey("one_partition_asset")

        @op
        def materialize():
            yield AssetMaterialization(b)
            yield AssetMaterialization(c, partition="a")
            yield AssetMaterialization(c, partition="b")
            yield AssetObservation(a, partition="a")
            yield Output(None)

        @op
        def materialize_two():
            yield AssetMaterialization(d, partition="x")
            yield AssetMaterialization(c, partition="a")
            yield Output(None)

        @op
        def materialize_three():
            yield AssetMaterialization(c, partition="c")
            yield Output(None)

        with instance_for_test() as created_instance:
            if not storage.has_instance:
                storage.register_instance(created_instance)

            run_id_1 = make_new_run_id()
            run_id_2 = make_new_run_id()
            run_id_3 = make_new_run_id()
            run_id_4 = make_new_run_id()

            with create_and_delete_test_runs(instance, [run_id_1, run_id_2, run_id_3]):
                cursor_run1 = _store_materialization_events(
                    storage, materialize, created_instance, run_id_1
                )
                assert storage.get_materialized_partitions(a) == set()
                assert storage.get_materialized_partitions(b) == set()
                assert storage.get_materialized_partitions(c) == {"a", "b"}

                cursor_run2 = _store_materialization_events(
                    storage, materialize_two, created_instance, run_id_2
                )
                _store_materialization_events(
                    storage, materialize_three, created_instance, run_id_3
                )

                # test that the cursoring logic works
                assert storage.get_materialized_partitions(a) == set()
                assert storage.get_materialized_partitions(b) == set()
                assert storage.get_materialized_partitions(c) == {"a", "b", "c"}
                assert storage.get_materialized_partitions(d) == {"x"}
                assert storage.get_materialized_partitions(a, before_cursor=cursor_run1) == set()
                assert storage.get_materialized_partitions(b, before_cursor=cursor_run1) == set()
                assert storage.get_materialized_partitions(c, before_cursor=cursor_run1) == {
                    "a",
                    "b",
                }
                assert storage.get_materialized_partitions(d, before_cursor=cursor_run1) == set()
                assert storage.get_materialized_partitions(a, after_cursor=cursor_run1) == set()
                assert storage.get_materialized_partitions(b, after_cursor=cursor_run1) == set()
                assert storage.get_materialized_partitions(c, after_cursor=cursor_run1) == {
                    "a",
                    "c",
                }
                assert storage.get_materialized_partitions(d, after_cursor=cursor_run1) == {"x"}
                assert (
                    storage.get_materialized_partitions(
                        a, before_cursor=cursor_run2, after_cursor=cursor_run1
                    )
                    == set()
                )
                assert (
                    storage.get_materialized_partitions(
                        b, before_cursor=cursor_run2, after_cursor=cursor_run1
                    )
                    == set()
                )
                assert storage.get_materialized_partitions(
                    c, before_cursor=cursor_run2, after_cursor=cursor_run1
                ) == {"a"}
                assert storage.get_materialized_partitions(
                    d, before_cursor=cursor_run2, after_cursor=cursor_run1
                ) == {"x"}
                assert storage.get_materialized_partitions(a, after_cursor=9999999999) == set()
                assert storage.get_materialized_partitions(b, after_cursor=9999999999) == set()
                assert storage.get_materialized_partitions(c, after_cursor=9999999999) == set()
                assert storage.get_materialized_partitions(d, after_cursor=9999999999) == set()

                # wipe asset, make sure we respect that
                if self.can_wipe():
                    storage.wipe_asset(c)
                    assert storage.get_materialized_partitions(c) == set()

                    _store_materialization_events(
                        storage, materialize_two, created_instance, run_id_4
                    )

                    assert storage.get_materialized_partitions(c) == {"a"}
                    assert storage.get_materialized_partitions(d) == {"x"}

                    # make sure adding an after_cursor doesn't mess with the wiped events
                    assert storage.get_materialized_partitions(c, after_cursor=9999999999) == set()
                    assert storage.get_materialized_partitions(d, after_cursor=9999999999) == set()

    def test_get_latest_storage_ids_by_partition(self, storage, instance):
        a = AssetKey(["a"])
        b = AssetKey(["b"])
        run_id = make_new_run_id()

        def _assert_storage_matches(expected):
            assert (
                storage.get_latest_storage_id_by_partition(
                    a, DagsterEventType.ASSET_MATERIALIZATION
                )
                == expected
            )

        def _store_partition_event(asset_key, partition) -> int:
            storage.store_event(
                EventLogEntry(
                    error_info=None,
                    level="debug",
                    user_message="",
                    run_id=run_id,
                    timestamp=time.time(),
                    dagster_event=DagsterEvent(
                        DagsterEventType.ASSET_MATERIALIZATION.value,
                        "nonce",
                        event_specific_data=StepMaterializationData(
                            AssetMaterialization(asset_key=asset_key, partition=partition)
                        ),
                    ),
                )
            )
            # get the storage id of the materialization we just stored
            return storage.get_event_records(
                EventRecordsFilter(DagsterEventType.ASSET_MATERIALIZATION),
                limit=1,
                ascending=False,
            )[0].storage_id

        with create_and_delete_test_runs(instance, [run_id]):
            latest_storage_ids = {}
            # no events
            _assert_storage_matches(latest_storage_ids)

            # p1 materialized
            latest_storage_ids["p1"] = _store_partition_event(a, "p1")
            _assert_storage_matches(latest_storage_ids)

            # p2 materialized
            latest_storage_ids["p2"] = _store_partition_event(a, "p2")
            _assert_storage_matches(latest_storage_ids)

            # unrelated asset materialized
            _store_partition_event(b, "p1")
            _store_partition_event(b, "p2")
            _assert_storage_matches(latest_storage_ids)

            # p1 re materialized
            latest_storage_ids["p1"] = _store_partition_event(a, "p1")
            _assert_storage_matches(latest_storage_ids)

            # p2 materialized
            latest_storage_ids["p3"] = _store_partition_event(a, "p3")
            _assert_storage_matches(latest_storage_ids)

            if self.can_wipe():
                storage.wipe_asset(a)
                latest_storage_ids = {}
                _assert_storage_matches(latest_storage_ids)

                latest_storage_ids["p1"] = _store_partition_event(a, "p1")
                _assert_storage_matches(latest_storage_ids)

    @pytest.mark.parametrize(
        "dagster_event_type",
        [DagsterEventType.ASSET_OBSERVATION, DagsterEventType.ASSET_MATERIALIZATION],
    )
    def test_get_latest_tags_by_partition(self, storage, instance, dagster_event_type):
        a = AssetKey(["a"])
        b = AssetKey(["b"])
        run_id = make_new_run_id()

        def _store_partition_event(asset_key, partition, tags) -> int:
            if dagster_event_type == DagsterEventType.ASSET_MATERIALIZATION:
                dagster_event = DagsterEvent(
                    dagster_event_type.value,
                    "nonce",
                    event_specific_data=StepMaterializationData(
                        AssetMaterialization(asset_key=asset_key, partition=partition, tags=tags)
                    ),
                )
            else:
                dagster_event = DagsterEvent(
                    dagster_event_type.value,
                    "nonce",
                    event_specific_data=AssetObservationData(
                        AssetObservation(asset_key=asset_key, partition=partition, tags=tags)
                    ),
                )

            storage.store_event(
                EventLogEntry(
                    error_info=None,
                    level="debug",
                    user_message="",
                    run_id=run_id,
                    timestamp=time.time(),
                    dagster_event=dagster_event,
                )
            )
            # get the storage id of the materialization we just stored
            return storage.get_event_records(
                EventRecordsFilter(dagster_event_type),
                limit=1,
                ascending=False,
            )[0].storage_id

        with create_and_delete_test_runs(instance, [run_id]):
            # no events
            assert (
                storage.get_latest_tags_by_partition(
                    a, dagster_event_type, tag_keys=["dagster/a", "dagster/b"]
                )
                == {}
            )

            # p1 materialized
            _store_partition_event(a, "p1", tags={"dagster/a": "1", "dagster/b": "1"})

            # p2 materialized
            _store_partition_event(a, "p2", tags={"dagster/a": "1", "dagster/b": "1"})

            # unrelated asset materialized
            t1 = _store_partition_event(b, "p1", tags={"dagster/a": "...", "dagster/b": "..."})
            _store_partition_event(b, "p2", tags={"dagster/a": "...", "dagster/b": "..."})

            # p1 re materialized
            _store_partition_event(a, "p1", tags={"dagster/a": "2", "dagster/b": "2"})

            # p3 materialized
            _store_partition_event(a, "p3", tags={"dagster/a": "1", "dagster/b": "1"})

            # no valid tag keys
            assert (
                storage.get_latest_tags_by_partition(a, dagster_event_type, tag_keys=["foo"]) == {}
            )

            # subset of existing tag keys
            assert storage.get_latest_tags_by_partition(
                a, dagster_event_type, tag_keys=["dagster/a"]
            ) == {
                "p1": {"dagster/a": "2"},
                "p2": {"dagster/a": "1"},
                "p3": {"dagster/a": "1"},
            }

            # superset of existing tag keys
            assert storage.get_latest_tags_by_partition(
                a,
                dagster_event_type,
                tag_keys=["dagster/a", "dagster/b", "dagster/c"],
            ) == {
                "p1": {"dagster/a": "2", "dagster/b": "2"},
                "p2": {"dagster/a": "1", "dagster/b": "1"},
                "p3": {"dagster/a": "1", "dagster/b": "1"},
            }

            # subset of existing partition keys
            assert storage.get_latest_tags_by_partition(
                a,
                dagster_event_type,
                tag_keys=["dagster/a", "dagster/b"],
                asset_partitions=["p1"],
            ) == {
                "p1": {"dagster/a": "2", "dagster/b": "2"},
            }

            # superset of existing partition keys
            assert storage.get_latest_tags_by_partition(
                a,
                dagster_event_type,
                tag_keys=["dagster/a", "dagster/b"],
                asset_partitions=["p1", "p2", "p3", "p4"],
            ) == {
                "p1": {"dagster/a": "2", "dagster/b": "2"},
                "p2": {"dagster/a": "1", "dagster/b": "1"},
                "p3": {"dagster/a": "1", "dagster/b": "1"},
            }

            # before p1 rematerialized and p3 existed
            assert storage.get_latest_tags_by_partition(
                a,
                dagster_event_type,
                tag_keys=["dagster/a", "dagster/b"],
                before_cursor=t1,
            ) == {
                "p1": {"dagster/a": "1", "dagster/b": "1"},
                "p2": {"dagster/a": "1", "dagster/b": "1"},
            }

            # shouldn't include p2's materialization
            assert storage.get_latest_tags_by_partition(
                a,
                dagster_event_type,
                tag_keys=["dagster/a", "dagster/b"],
                after_cursor=t1,
            ) == {
                "p1": {"dagster/a": "2", "dagster/b": "2"},
                "p3": {"dagster/a": "1", "dagster/b": "1"},
            }

            if self.can_wipe():
                storage.wipe_asset(a)
                assert (
                    storage.get_latest_tags_by_partition(
                        a,
                        dagster_event_type,
                        tag_keys=["dagster/a", "dagster/b"],
                    )
                    == {}
                )
                _store_partition_event(a, "p1", tags={"dagster/a": "3", "dagster/b": "3"})
                assert storage.get_latest_tags_by_partition(
                    a, dagster_event_type, tag_keys=["dagster/a", "dagster/b"]
                ) == {
                    "p1": {"dagster/a": "3", "dagster/b": "3"},
                }

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

    def test_store_asset_materialization_planned_event_with_invalid_partitions_subset(
        self, storage, instance
    ) -> None:
        a = AssetKey(["a"])
        run_id_1 = make_new_run_id()

        partitions_def = DailyPartitionsDefinition("2023-01-01")
        partitions_subset = (
            external_partitions_definition_from_def(partitions_def)
            .get_partitions_definition()
            .subset_with_partition_keys(
                partitions_def.get_partition_keys_in_range(
                    PartitionKeyRange("2023-01-05", "2023-01-10")
                )
            )
        )
        assert isinstance(partitions_subset, PartitionKeysTimeWindowPartitionsSubset)

        with create_and_delete_test_runs(instance, [run_id_1]):
            with pytest.raises(
                CheckError,
                match="partitions_subset must be serializable",
            ):
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
                            event_specific_data=AssetMaterializationPlannedData(
                                a, partitions_subset=partitions_subset
                            ),
                        ),
                    )
                )

            with pytest.raises(
                DagsterInvariantViolationError,
                match="Cannot provide both partition and partitions_subset",
            ):
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
                            event_specific_data=AssetMaterializationPlannedData(
                                a, partitions_subset=partitions_subset, partition="foo"
                            ),
                        ),
                    )
                )

    def test_store_asset_materialization_planned_event_with_partitions_subset(
        self, storage, instance
    ) -> None:
        a = AssetKey(["a"])
        run_id_1 = make_new_run_id()

        partitions_def = DailyPartitionsDefinition("2023-01-01")
        partitions_subset = (
            external_partitions_definition_from_def(partitions_def)
            .get_partitions_definition()
            .subset_with_partition_keys(
                partitions_def.get_partition_keys_in_range(
                    PartitionKeyRange("2023-01-05", "2023-01-10")
                )
            )
            .to_serializable_subset()
        )

        with create_and_delete_test_runs(instance, [run_id_1]):
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
                        event_specific_data=AssetMaterializationPlannedData(
                            a, partitions_subset=partitions_subset
                        ),
                    ),
                )
            )

            records = storage.get_event_records(
                EventRecordsFilter(
                    event_type=DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
                    asset_key=a,
                )
            )
            assert len(records) == 1
            record = records[0]
            assert record.partition_key is None
            assert record.event_log_entry.dagster_event.partitions_subset == partitions_subset

            info = storage.get_latest_planned_materialization_info(asset_key=a)
            assert info
            assert info.run_id == run_id_1

    def test_get_latest_planned_materialization_info(self, storage, instance):
        a = AssetKey(["a"])
        b = AssetKey(["b"])
        run_id_1 = make_new_run_id()
        run_id_2 = make_new_run_id()

        with create_and_delete_test_runs(instance, [run_id_1, run_id_2]):
            # store planned event for a
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
                        event_specific_data=AssetMaterializationPlannedData(a),
                    ),
                )
            )
            # store unplanned mat for b
            storage.store_event(
                EventLogEntry(
                    error_info=None,
                    level="debug",
                    user_message="",
                    run_id=run_id_2,
                    timestamp=time.time(),
                    dagster_event=DagsterEvent(
                        DagsterEventType.ASSET_MATERIALIZATION.value,
                        "nonce",
                        event_specific_data=StepMaterializationData(
                            AssetMaterialization(asset_key=a)
                        ),
                    ),
                )
            )

            info = storage.get_latest_planned_materialization_info(asset_key=a)
            assert info and info.storage_id
            info = storage.get_latest_planned_materialization_info(asset_key=b)
            assert not info

    def test_get_latest_planned_materialization_info_partitioned(self, storage, instance):
        a = AssetKey(["a"])
        b = AssetKey(["b"])
        run_id_1 = make_new_run_id()
        run_id_2 = make_new_run_id()

        with create_and_delete_test_runs(instance, [run_id_1, run_id_2]):
            # store planned event for a
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
                        event_specific_data=AssetMaterializationPlannedData(a, partition="foo"),
                    ),
                )
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
                        event_specific_data=AssetMaterializationPlannedData(a, partition="bar"),
                    ),
                )
            )
            # store unplanned mat for b
            storage.store_event(
                EventLogEntry(
                    error_info=None,
                    level="debug",
                    user_message="",
                    run_id=run_id_2,
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
            storage.store_event(
                EventLogEntry(
                    error_info=None,
                    level="debug",
                    user_message="",
                    run_id=run_id_2,
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

            foo_info = storage.get_latest_planned_materialization_info(asset_key=a, partition="foo")
            assert foo_info and foo_info.storage_id
            bar_info = storage.get_latest_planned_materialization_info(asset_key=a, partition="bar")
            assert bar_info and bar_info.storage_id
            assert bar_info.storage_id != foo_info.storage_id

            # assert unplanned materializations don't affect planned materializations
            assert not storage.get_latest_planned_materialization_info(asset_key=b, partition="foo")

    def test_partitions_methods_on_materialization_planned_event_with_partitions_subset(
        self, storage, instance
    ) -> None:
        a = AssetKey(["a"])
        gen_events_run_id = make_new_run_id()
        subset_event_run_id = make_new_run_id()

        @op
        def gen_op():
            yield AssetMaterialization(asset_key=a, partition="2023-01-05")
            yield Output(1)

        partitions_def = DailyPartitionsDefinition("2023-01-01")
        partitions_subset = (
            external_partitions_definition_from_def(partitions_def)
            .get_partitions_definition()
            .subset_with_partition_keys(
                partitions_def.get_partition_keys_in_range(
                    PartitionKeyRange("2023-01-05", "2023-01-06")
                )
            )
            .to_serializable_subset()
        )

        with instance_for_test() as created_instance:
            if not storage.has_instance:
                storage.register_instance(created_instance)

            with create_and_delete_test_runs(instance, [gen_events_run_id, subset_event_run_id]):
                events_one, _ = _synthesize_events(
                    lambda: gen_op(), instance=created_instance, run_id=gen_events_run_id
                )
                for event in events_one:
                    storage.store_event(event)

                storage.store_event(
                    EventLogEntry(
                        error_info=None,
                        level="debug",
                        user_message="",
                        run_id=subset_event_run_id,
                        timestamp=time.time(),
                        dagster_event=DagsterEvent(
                            DagsterEventType.ASSET_MATERIALIZATION_PLANNED.value,
                            "nonce",
                            event_specific_data=AssetMaterializationPlannedData(
                                a, partition="2023-01-05"
                            ),
                        ),
                    )
                )
                storage.store_event(
                    EventLogEntry(
                        error_info=None,
                        level="debug",
                        user_message="",
                        run_id=subset_event_run_id,
                        timestamp=time.time(),
                        dagster_event=DagsterEvent(
                            DagsterEventType.ASSET_MATERIALIZATION_PLANNED.value,
                            "nonce",
                            event_specific_data=AssetMaterializationPlannedData(
                                a, partitions_subset=partitions_subset
                            ),
                        ),
                    )
                )

                records = storage.get_event_records(
                    EventRecordsFilter(
                        event_type=DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
                        asset_key=a,
                    ),
                    ascending=True,
                )
                assert len(records) == 2
                single_partition_event = records[0]
                assert (
                    single_partition_event.event_log_entry.dagster_event.partition == "2023-01-05"
                )

                partitions_subset_event = records[1]
                event_id = partitions_subset_event.storage_id
                assert partitions_subset_event.partition_key is None
                assert (
                    partitions_subset_event.event_log_entry.dagster_event.partitions_subset
                    == partitions_subset
                )

                assert storage.get_materialized_partitions(a) == {"2023-01-05"}
                planned_but_no_materialization_partitions = storage.get_latest_asset_partition_materialization_attempts_without_materializations(
                    a
                )
                if self.has_asset_partitions_table():
                    # When an asset partitions table is present we can fetch planned but not
                    # materialized partitions when planned events target a partitions subset
                    assert len(planned_but_no_materialization_partitions) == 2
                    assert planned_but_no_materialization_partitions.keys() == {
                        "2023-01-05",
                        "2023-01-06",
                    }
                    assert planned_but_no_materialization_partitions["2023-01-05"] == (
                        subset_event_run_id,
                        event_id,
                    )
                    assert planned_but_no_materialization_partitions["2023-01-06"] == (
                        subset_event_run_id,
                        event_id,
                    )

                else:
                    # When an asset partitions table is not present we can only fetch planned but
                    # not materialized partitions when planned events target a single partition
                    assert planned_but_no_materialization_partitions.keys() == {"2023-01-05"}
                    assert planned_but_no_materialization_partitions["2023-01-05"] == (
                        subset_event_run_id,
                        single_partition_event.storage_id,
                    )

                    # When asset partitions table is not present get_latest_storage_id_by_partition
                    # only returns storage IDs for single-partition events
                    latest_storage_id_by_partition = storage.get_latest_storage_id_by_partition(
                        a, DagsterEventType.ASSET_MATERIALIZATION_PLANNED
                    )
                    assert latest_storage_id_by_partition == {
                        "2023-01-05": single_partition_event.storage_id
                    }

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
            assert (
                storage.get_latest_asset_partition_materialization_attempts_without_materializations(
                    a
                )
                == {
                    "foo": (run_id_1, records[1].storage_id),
                    "bar": (run_id_2, records[0].storage_id),
                }
            )
            assert (
                storage.get_latest_asset_partition_materialization_attempts_without_materializations(
                    a, records[1].storage_id
                )
                == {
                    "bar": (run_id_2, records[0].storage_id),
                }
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
                        event_specific_data=AssetMaterializationPlannedData(a, "bar"),
                    ),
                )
            )

            assert (
                storage.get_latest_asset_partition_materialization_attempts_without_materializations(
                    a
                )
                == {
                    "foo": (run_id_1, records[1].storage_id),
                    "bar": (run_id_3, records[0].storage_id + 1),
                }
            )

    def test_get_observation(self, storage: EventLogStorage, test_run_id: str):
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

            # legacy API
            records = storage.get_event_records(
                EventRecordsFilter(
                    event_type=DagsterEventType.ASSET_OBSERVATION,
                    asset_key=a,
                )
            )

            assert len(records) == 1

            # new API
            result = storage.fetch_observations(a, limit=100)
            assert isinstance(result, EventRecordsResult)
            assert len(result.records) == 1
            record = result.records[0]
            assert record.event_log_entry.dagster_event
            assert record.event_log_entry.dagster_event.asset_key == a
            assert result.cursor == EventLogCursor.from_storage_id(record.storage_id).to_string()

    def test_get_planned_materialization(self, storage: EventLogStorage, test_run_id: str):
        a = AssetKey(["key_a"])

        storage.store_event(
            EventLogEntry(
                error_info=None,
                level="debug",
                user_message="",
                run_id=test_run_id,
                timestamp=time.time(),
                dagster_event=DagsterEvent(
                    DagsterEventType.ASSET_MATERIALIZATION_PLANNED.value,
                    "nonce",
                    event_specific_data=AssetMaterializationPlannedData(a, "foo"),
                ),
            )
        )

        # legacy API
        records = storage.get_event_records(
            EventRecordsFilter(
                event_type=DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
                asset_key=a,
            )
        )
        assert len(records) == 1
        assert records[0].partition_key == "foo"
        foo_record = records[0]

        # unpartitioned query
        unpartitioned_info = storage.get_latest_planned_materialization_info(asset_key=a)
        assert unpartitioned_info
        assert unpartitioned_info.run_id == test_run_id
        assert unpartitioned_info.storage_id == foo_record.storage_id

        # matching partitioned query
        foo_info = storage.get_latest_planned_materialization_info(asset_key=a, partition="foo")
        assert foo_info
        assert foo_info.run_id == test_run_id
        assert foo_info.storage_id == unpartitioned_info.storage_id

        # unmatched partitioned query
        bar_info = storage.get_latest_planned_materialization_info(asset_key=a, partition="bar")
        assert bar_info is None

        # store "bar" partition
        storage.store_event(
            EventLogEntry(
                error_info=None,
                level="debug",
                user_message="",
                run_id=test_run_id,
                timestamp=time.time(),
                dagster_event=DagsterEvent(
                    DagsterEventType.ASSET_MATERIALIZATION_PLANNED.value,
                    "nonce",
                    event_specific_data=AssetMaterializationPlannedData(a, "bar"),
                ),
            )
        )

        # legacy API
        records = storage.get_event_records(
            EventRecordsFilter(
                event_type=DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
                asset_key=a,
            )
        )
        assert len(records) == 2
        assert records[0].partition_key == "bar"
        bar_record = records[0]

        # unpartitioned query
        unpartitioned_info = storage.get_latest_planned_materialization_info(asset_key=a)
        assert unpartitioned_info
        assert unpartitioned_info.run_id == test_run_id
        assert unpartitioned_info.storage_id == bar_record.storage_id

        # foo partitioned query
        foo_info = storage.get_latest_planned_materialization_info(asset_key=a, partition="foo")
        assert foo_info
        assert foo_info.run_id == test_run_id
        assert foo_info.storage_id == foo_record.storage_id

        # bar partitioned query
        bar_info = storage.get_latest_planned_materialization_info(asset_key=a, partition="bar")
        assert bar_info
        assert bar_info.run_id == test_run_id
        assert bar_info.storage_id == bar_record.storage_id

    def test_asset_key_exists_on_observation(
        self,
        storage: EventLogStorage,
        instance: DagsterInstance,
    ):
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

    def test_filter_on_storage_ids(
        self,
        storage: EventLogStorage,
        instance: DagsterInstance,
        test_run_id: str,
    ):
        a = AssetKey(["key_a"])

        @op
        def gen_op():
            yield AssetMaterialization(asset_key=a, metadata={"foo": "bar"})
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
                    event_type=DagsterEventType.ASSET_MATERIALIZATION,
                    asset_key=a,
                )
            )
            assert len(records) == 1
            storage_id = records[0].storage_id

            records = storage.get_event_records(
                EventRecordsFilter(
                    event_type=DagsterEventType.ASSET_MATERIALIZATION, storage_ids=[storage_id]
                )
            )
            assert len(records) == 1
            assert records[0].storage_id == storage_id

            # Assert that not providing storage IDs to filter on will still fetch events
            assert (
                len(
                    storage.get_event_records(
                        EventRecordsFilter(
                            event_type=DagsterEventType.ASSET_MATERIALIZATION,
                        )
                    )
                )
                == 1
            )

    def test_get_asset_records(
        self,
        storage: EventLogStorage,
        instance: DagsterInstance,
    ):
        @asset
        def my_asset():
            return 1

        @asset
        def second_asset(my_asset):
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
                defs = Definitions(
                    assets=[my_asset, second_asset],
                    jobs=[
                        define_asset_job("one_asset_job", ["my_asset"]),
                        define_asset_job("two_asset_job"),
                    ],
                )
                result = _execute_job_and_store_events(
                    created_instance,
                    storage,
                    defs.get_job_def("one_asset_job"),
                    run_id=run_id_1,
                )
                records = storage.get_asset_records([my_asset_key])

                assert len(records) == 1
                asset_entry = records[0].asset_entry
                assert asset_entry.asset_key == my_asset_key
                materialize_event = next(
                    event for event in result.all_events if event.is_step_materialization
                )
                assert asset_entry.last_materialization
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
                        defs.get_job_def("two_asset_job"),
                        run_id=run_id_2,
                    )
                    records = storage.get_asset_records([my_asset_key])
                    assert len(records) == 1
                    records = storage.get_asset_records([])  # should select no assets
                    assert len(records) == 0
                    records = storage.get_asset_records()  # should select all assets
                    assert len(records) == 2

                    records = list(records)
                    records.sort(
                        key=lambda record: record.asset_entry.asset_key
                    )  # order by asset key
                    asset_entry = records[0].asset_entry
                    assert asset_entry.asset_key == my_asset_key
                    materialize_event = next(
                        event for event in result.all_events if event.is_step_materialization
                    )
                    assert asset_entry.last_materialization
                    assert asset_entry.last_materialization.dagster_event == materialize_event
                    assert asset_entry.last_run_id == result.run_id
                    assert isinstance(asset_entry.asset_details, AssetDetails)

    def test_asset_record_run_id_wiped(
        self,
        storage: EventLogStorage,
        instance: DagsterInstance,
    ):
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

    def test_last_run_id_updates_on_materialization_planned(
        self,
        storage: EventLogStorage,
        instance: DagsterInstance,
    ):
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
                never_materializes_job = Definitions(
                    assets=[never_materializes_asset],
                ).get_implicit_global_asset_job_def()

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

    def test_get_logs_for_all_runs_by_log_id_of_type(self, storage: EventLogStorage):
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

    def test_get_logs_for_all_runs_by_log_id_cursor(self, storage: EventLogStorage):
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

    def test_get_logs_for_all_runs_by_log_id_limit(self, storage: EventLogStorage):
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

    def test_get_maximum_record_id(self, storage: EventLogStorage):
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

    def test_get_materialization_tag(
        self,
        storage: EventLogStorage,
        instance: DagsterInstance,
    ):
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

        # after the runs are deleted, the event tags should not persist
        storage.delete_events(run_id)
        asset_event_tags = storage.get_event_tags_for_asset(key)
        assert asset_event_tags == []

    def test_add_asset_event_tags(
        self,
        storage: EventLogStorage,
        instance: DagsterInstance,
    ):
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
            assert mat_record.asset_key
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

    def test_add_asset_event_tags_initially_empty(
        self,
        storage: EventLogStorage,
        instance: DagsterInstance,
    ):
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
            assert mat_record.asset_key
            storage.add_asset_event_tags(
                event_id=mat_record.storage_id,
                event_timestamp=mat_record.event_log_entry.timestamp,
                asset_key=mat_record.asset_key,
                new_tags={"a": "apple", "b": "boot"},
            )

            assert storage.get_event_tags_for_asset(key, filter_event_id=mat_record.storage_id) == [
                {"a": "apple", "b": "boot"}
            ]

    def test_materialization_tag_on_wipe(
        self,
        storage: EventLogStorage,
        instance: DagsterInstance,
    ):
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

    def test_event_record_filter_tags(
        self,
        storage: EventLogStorage,
        instance: DagsterInstance,
    ):
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
                assert record.event_log_entry.dagster_event
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
                assert record.event_log_entry.dagster_event
                materialization = (
                    record.event_log_entry.dagster_event.step_materialization_data.materialization
                )
                assert isinstance(materialization.partition, MultiPartitionKey)
                date_dimension = next(
                    dimension
                    for dimension in materialization.partition.dimension_keys
                    if dimension.dimension_name == "date"
                )
                assert date_dimension.partition_key == "2022-10-13"

    def test_event_records_filter_tags_requires_asset_key(self, storage):
        with pytest.raises(Exception, match="Asset key must be set in event records"):
            storage.get_event_records(
                EventRecordsFilter(
                    DagsterEventType.ASSET_MATERIALIZATION,
                    tags={"dagster/partition/date": "2022-10-13"},
                )
            )

    def test_multi_partitions_partition_deserialization(
        self,
        storage: EventLogStorage,
        instance: DagsterInstance,
    ):
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

            assert created_instance.get_materialized_partitions(key) == {
                MultiPartitionKey({"country": "US", "date": "2022-10-13"}),
                MultiPartitionKey({"country": "Mexico", "date": "2022-10-14"}),
                MultiPartitionKey({"country": "Canada", "date": "2022-10-13"}),
            }

    def test_store_and_wipe_cached_status(
        self,
        storage: EventLogStorage,
        instance: DagsterInstance,
    ):
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
                serialized_in_progress_partition_subset="qux",
                earliest_in_progress_materialization_event_id=42,
            )

            # Check that AssetStatusCacheValue has all fields set. This ensures that we test that the
            # cloud gql representation is complete.
            for field in cache_value._fields:
                assert getattr(cache_value, field) is not None

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
                cache_value = AssetStatusCacheValue(
                    latest_storage_id=1,
                    partitions_def_id=None,
                    serialized_materialized_partition_subset=None,
                )
                storage.update_asset_cached_status_data(
                    asset_key=asset_key, cache_values=cache_value
                )
                assert _get_cached_status_for_asset(storage, asset_key) == cache_value
                record = storage.get_asset_records([asset_key])[0]
                storage.wipe_asset_cached_status(asset_key)
                assert _get_cached_status_for_asset(storage, asset_key) is None
                post_wipe_record = storage.get_asset_records([asset_key])[0]
                assert (
                    record.asset_entry.last_materialization_record
                    == post_wipe_record.asset_entry.last_materialization_record
                )
                assert record.asset_entry.last_run_id == post_wipe_record.asset_entry.last_run_id

                storage.wipe_asset(asset_key)
                assert storage.get_asset_records() == []

                events, _ = _synthesize_events(
                    lambda: yields_materialization(),
                    run_id=run_id_2,
                )
                for event in events:
                    storage.store_event(event)

                assert _get_cached_status_for_asset(storage, asset_key) is None

    def test_add_dynamic_partitions(self, storage: EventLogStorage):
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

        # Adding no partitions is a no-op
        storage.add_dynamic_partitions(partitions_def_name="foo", partition_keys=[])

    def test_delete_dynamic_partitions(self, storage: EventLogStorage):
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

    def test_has_dynamic_partition(self, storage: EventLogStorage):
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

    def test_concurrency(self, storage: EventLogStorage):
        assert storage
        if not storage.supports_global_concurrency_limits:
            pytest.skip("storage does not support global op concurrency")

        if self.can_wipe():
            storage.wipe()

        run_id_one = make_new_run_id()
        run_id_two = make_new_run_id()
        run_id_three = make_new_run_id()

        def claim(key, run_id, step_key, priority=0):
            claim_status = storage.claim_concurrency_slot(key, run_id, step_key, priority)
            return claim_status.slot_status

        def pending_step_count(key):
            info = storage.get_concurrency_info(key)
            return info.pending_step_count

        def assigned_step_count(key):
            info = storage.get_concurrency_info(key)
            return info.assigned_step_count

        # initially there are no concurrency limited keys
        assert storage.get_concurrency_keys() == set()

        # fill concurrency slots
        storage.set_concurrency_slots("foo", 3)
        storage.set_concurrency_slots("bar", 1)

        # now there are two concurrency limited keys
        assert storage.get_concurrency_keys() == {"foo", "bar"}
        assert pending_step_count("foo") == 0
        assert assigned_step_count("foo") == 0
        assert pending_step_count("bar") == 0
        assert assigned_step_count("bar") == 0

        assert claim("foo", run_id_one, "step_1") == ConcurrencySlotStatus.CLAIMED
        assert claim("foo", run_id_two, "step_2") == ConcurrencySlotStatus.CLAIMED
        assert claim("foo", run_id_one, "step_3") == ConcurrencySlotStatus.CLAIMED
        assert claim("bar", run_id_two, "step_4") == ConcurrencySlotStatus.CLAIMED
        assert pending_step_count("foo") == 0
        assert assigned_step_count("foo") == 3
        assert pending_step_count("bar") == 0
        assert assigned_step_count("bar") == 1

        # next claim should be blocked
        assert claim("foo", run_id_three, "step_5") == ConcurrencySlotStatus.BLOCKED
        assert claim("bar", run_id_three, "step_6") == ConcurrencySlotStatus.BLOCKED
        assert pending_step_count("foo") == 1
        assert assigned_step_count("foo") == 3
        assert pending_step_count("bar") == 1
        assert assigned_step_count("bar") == 1

        # free single slot, one in each concurrency key: foo, bar
        storage.free_concurrency_slots_for_run(run_id_two)
        assert pending_step_count("foo") == 0
        assert assigned_step_count("foo") == 3
        assert pending_step_count("bar") == 0
        assert assigned_step_count("bar") == 1

        # try to claim again
        assert claim("foo", run_id_three, "step_5") == ConcurrencySlotStatus.CLAIMED
        assert claim("bar", run_id_three, "step_6") == ConcurrencySlotStatus.CLAIMED
        # new claims should be blocked
        assert claim("foo", run_id_three, "step_7") == ConcurrencySlotStatus.BLOCKED
        assert claim("foo", run_id_three, "step_8") == ConcurrencySlotStatus.BLOCKED

    def test_concurrency_priority(self, storage: EventLogStorage):
        if not storage.supports_global_concurrency_limits:
            pytest.skip("storage does not support global op concurrency")

        run_id = make_new_run_id()

        def claim(key, run_id, step_key, priority=0):
            claim_status = storage.claim_concurrency_slot(key, run_id, step_key, priority)
            return claim_status.slot_status

        if self.can_wipe():
            storage.wipe()

        storage.set_concurrency_slots("foo", 5)
        storage.set_concurrency_slots("bar", 1)

        # fill all the slots
        assert claim("foo", run_id, "step_1") == ConcurrencySlotStatus.CLAIMED
        assert claim("foo", run_id, "step_2") == ConcurrencySlotStatus.CLAIMED
        assert claim("foo", run_id, "step_3") == ConcurrencySlotStatus.CLAIMED
        assert claim("foo", run_id, "step_4") == ConcurrencySlotStatus.CLAIMED
        assert claim("foo", run_id, "step_5") == ConcurrencySlotStatus.CLAIMED

        # next claims should be blocked
        assert claim("foo", run_id, "a", 0) == ConcurrencySlotStatus.BLOCKED
        assert claim("foo", run_id, "b", 2) == ConcurrencySlotStatus.BLOCKED
        assert claim("foo", run_id, "c", 0) == ConcurrencySlotStatus.BLOCKED

        # free up a slot
        storage.free_concurrency_slot_for_step(run_id, "step_1")

        # a new step trying to claim foo should also be blocked
        assert claim("foo", run_id, "d", 0) == ConcurrencySlotStatus.BLOCKED

        # the claim calls for all the previously blocked steps should all remain blocked, except for
        # the highest priority one
        assert claim("foo", run_id, "a", 0) == ConcurrencySlotStatus.BLOCKED
        assert claim("foo", run_id, "c", 0) == ConcurrencySlotStatus.BLOCKED
        assert claim("foo", run_id, "d", 0) == ConcurrencySlotStatus.BLOCKED
        assert claim("foo", run_id, "b", 2) == ConcurrencySlotStatus.CLAIMED

        # free up another slot
        storage.free_concurrency_slot_for_step(run_id, "step_2")

        # the claim calls for all the previously blocked steps should all remain blocked, except for
        # the oldest of the zero priority pending steps
        assert claim("foo", run_id, "c", 0) == ConcurrencySlotStatus.BLOCKED
        assert claim("foo", run_id, "d", 0) == ConcurrencySlotStatus.BLOCKED
        assert claim("foo", run_id, "a", 0) == ConcurrencySlotStatus.CLAIMED

        # b, c remain of the previous set of pending steps
        # freeing up 3 slots means that trying to claim a new slot should go through, even though
        # b and c have not claimed a slot yet (whilst being assigned)
        storage.free_concurrency_slot_for_step(run_id, "step_3")
        storage.free_concurrency_slot_for_step(run_id, "step_4")
        storage.free_concurrency_slot_for_step(run_id, "step_5")

        assert claim("foo", run_id, "e") == ConcurrencySlotStatus.CLAIMED

    def test_concurrency_allocate_from_pending(self, storage: EventLogStorage):
        if not storage.supports_global_concurrency_limits:
            pytest.skip("storage does not support global op concurrency")

        if self.can_wipe():
            storage.wipe()

        run_id = make_new_run_id()

        def claim(key, run_id, step_key, priority=0):
            claim_status = storage.claim_concurrency_slot(key, run_id, step_key, priority)
            return claim_status.slot_status

        storage.set_concurrency_slots("foo", 1)

        # fill
        assert claim("foo", run_id, "a") == ConcurrencySlotStatus.CLAIMED
        assert claim("foo", run_id, "b") == ConcurrencySlotStatus.BLOCKED
        assert claim("foo", run_id, "c") == ConcurrencySlotStatus.BLOCKED
        assert claim("foo", run_id, "d") == ConcurrencySlotStatus.BLOCKED
        assert claim("foo", run_id, "e") == ConcurrencySlotStatus.BLOCKED

        # there is only one claimed slot, the rest are pending
        foo_info = storage.get_concurrency_info("foo")
        assert foo_info.active_slot_count == 1
        assert foo_info.active_run_ids == {run_id}
        assert len(foo_info.claimed_slots) == 1
        assert foo_info.claimed_slots[0].step_key == "a"
        assert len(foo_info.pending_steps) == 5
        assigned_steps = [step for step in foo_info.pending_steps if step.assigned_timestamp]
        assert len(assigned_steps) == 1
        assert assigned_steps[0].step_key == "a"

        # a is assigned, has the active slot, the rest are not assigned
        assert storage.check_concurrency_claim("foo", run_id, "a").assigned_timestamp is not None
        assert storage.check_concurrency_claim("foo", run_id, "b").assigned_timestamp is None
        assert storage.check_concurrency_claim("foo", run_id, "c").assigned_timestamp is None
        assert storage.check_concurrency_claim("foo", run_id, "d").assigned_timestamp is None
        assert storage.check_concurrency_claim("foo", run_id, "e").assigned_timestamp is None

        # now, allocate another slot
        storage.set_concurrency_slots("foo", 2)

        # there is still only one claimed slot, but now there are to assigned steps (a,b)
        foo_info = storage.get_concurrency_info("foo")
        assert foo_info.active_slot_count == 1
        assert foo_info.active_run_ids == {run_id}

        assert storage.check_concurrency_claim("foo", run_id, "a").assigned_timestamp is not None
        assert storage.check_concurrency_claim("foo", run_id, "b").assigned_timestamp is not None
        assert storage.check_concurrency_claim("foo", run_id, "c").assigned_timestamp is None
        assert storage.check_concurrency_claim("foo", run_id, "d").assigned_timestamp is None
        assert storage.check_concurrency_claim("foo", run_id, "e").assigned_timestamp is None

        # free the assigned b slot (which has never actually claimed the slot)
        storage.free_concurrency_slot_for_step(run_id, "b")

        # we should assigned the open slot to c slot
        assert storage.check_concurrency_claim("foo", run_id, "a").assigned_timestamp is not None
        assert storage.check_concurrency_claim("foo", run_id, "c").assigned_timestamp is not None
        assert storage.check_concurrency_claim("foo", run_id, "d").assigned_timestamp is None
        assert storage.check_concurrency_claim("foo", run_id, "e").assigned_timestamp is None

    def test_invalid_concurrency_limit(self, storage: EventLogStorage):
        if not storage.supports_global_concurrency_limits:
            pytest.skip("storage does not support global op concurrency")

        with pytest.raises(DagsterInvalidInvocationError):
            storage.set_concurrency_slots("foo", -1)

        with pytest.raises(DagsterInvalidInvocationError):
            storage.set_concurrency_slots("foo", 1001)

    def test_slot_downsize(self, storage: EventLogStorage):
        if not storage.supports_global_concurrency_limits:
            pytest.skip("storage does not support global op concurrency")

        if self.can_wipe():
            storage.wipe()

        run_id = make_new_run_id()

        def claim(key, run_id, step_key, priority=0):
            claim_status = storage.claim_concurrency_slot(key, run_id, step_key, priority)
            return claim_status.slot_status

        # set concurrency slots
        storage.set_concurrency_slots("foo", 5)

        # fill em partially up
        assert claim("foo", run_id, "a") == ConcurrencySlotStatus.CLAIMED
        assert claim("foo", run_id, "b") == ConcurrencySlotStatus.CLAIMED
        assert claim("foo", run_id, "c") == ConcurrencySlotStatus.CLAIMED

        storage.set_concurrency_slots("foo", 1)

        assert storage.check_concurrency_claim("foo", run_id, "a").is_claimed
        assert storage.check_concurrency_claim("foo", run_id, "b").is_claimed
        assert storage.check_concurrency_claim("foo", run_id, "c").is_claimed
        foo_info = storage.get_concurrency_info("foo")

        # the slot count is 1, but the active slot count is 3 and will remain so until the slots
        # are freed
        assert foo_info.slot_count == 1
        assert foo_info.active_slot_count == 3

    def test_slot_upsize(self, storage: EventLogStorage):
        if not storage.supports_global_concurrency_limits:
            pytest.skip("storage does not support global op concurrency")

        if self.can_wipe():
            storage.wipe()

        run_id = make_new_run_id()

        def claim(key, run_id, step_key, priority=0):
            claim_status = storage.claim_concurrency_slot(key, run_id, step_key, priority)
            return claim_status.slot_status

        # set concurrency slots
        storage.set_concurrency_slots("foo", 1)

        # fill em partially up
        assert claim("foo", run_id, "a") == ConcurrencySlotStatus.CLAIMED
        assert claim("foo", run_id, "b") == ConcurrencySlotStatus.BLOCKED
        assert claim("foo", run_id, "c") == ConcurrencySlotStatus.BLOCKED
        assert claim("foo", run_id, "d") == ConcurrencySlotStatus.BLOCKED
        assert claim("foo", run_id, "e") == ConcurrencySlotStatus.BLOCKED

        assert storage.check_concurrency_claim("foo", run_id, "a").is_claimed
        assert not storage.check_concurrency_claim("foo", run_id, "b").is_assigned
        assert not storage.check_concurrency_claim("foo", run_id, "c").is_assigned
        assert not storage.check_concurrency_claim("foo", run_id, "d").is_assigned
        assert not storage.check_concurrency_claim("foo", run_id, "e").is_assigned

        foo_info = storage.get_concurrency_info("foo")
        assert foo_info.slot_count == 1
        assert foo_info.active_slot_count == 1
        assert foo_info.pending_step_count == 4
        assert foo_info.assigned_step_count == 1  # the claimed step is assigned

        storage.set_concurrency_slots("foo", 4)

        assert storage.check_concurrency_claim("foo", run_id, "a").is_claimed
        assert storage.check_concurrency_claim("foo", run_id, "b").is_assigned
        assert storage.check_concurrency_claim("foo", run_id, "c").is_assigned
        assert storage.check_concurrency_claim("foo", run_id, "d").is_assigned
        assert not storage.check_concurrency_claim("foo", run_id, "e").is_assigned

        foo_info = storage.get_concurrency_info("foo")
        assert foo_info.slot_count == 4
        assert foo_info.active_slot_count == 1
        assert foo_info.pending_step_count == 1
        assert foo_info.assigned_step_count == 4

    def test_concurrency_run_ids(self, storage: EventLogStorage):
        if not storage.supports_global_concurrency_limits:
            pytest.skip("storage does not support global op concurrency")

        if not self.can_wipe():
            # this test requires wiping
            pytest.skip(
                "storage does not support reading run ids for the purpose of freeing concurrency"
                " slots"
            )

        storage.wipe()

        one = make_new_run_id()
        two = make_new_run_id()

        storage.set_concurrency_slots("foo", 1)

        storage.claim_concurrency_slot("foo", one, "a")
        storage.claim_concurrency_slot("foo", two, "b")
        storage.claim_concurrency_slot("foo", one, "c")

        assert storage.get_concurrency_run_ids() == {one, two}
        storage.free_concurrency_slots_for_run(one)
        assert storage.get_concurrency_run_ids() == {two}
        storage.delete_events(run_id=two)
        assert storage.get_concurrency_run_ids() == set()

    def test_threaded_concurrency(self, storage: EventLogStorage):
        if not storage.supports_global_concurrency_limits:
            pytest.skip("storage does not support global op concurrency")

        if self.can_wipe():
            storage.wipe()

        TOTAL_TIMEOUT_TIME = 30

        run_id = make_new_run_id()

        storage.set_concurrency_slots("foo", 5)

        def _occupy_slot(key: str):
            start = time.time()
            claim_status = storage.claim_concurrency_slot("foo", run_id, key)
            while time.time() < start + TOTAL_TIMEOUT_TIME:
                if claim_status.slot_status == ConcurrencySlotStatus.CLAIMED:
                    break
                else:
                    claim_status = storage.claim_concurrency_slot("foo", run_id, key)
                    time.sleep(0.05)
            storage.free_concurrency_slot_for_step(run_id, key)

        start = time.time()
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(_occupy_slot, str(i)) for i in range(100)]
            while not all(f.done() for f in futures) and time.time() < start + TOTAL_TIMEOUT_TIME:
                time.sleep(0.1)

            foo_info = storage.get_concurrency_info("foo")
            assert foo_info.slot_count == 5
            assert foo_info.active_slot_count == 0
            assert foo_info.pending_step_count == 0
            assert foo_info.assigned_step_count == 0

            assert all(f.done() for f in futures)

    def test_zero_concurrency(self, storage: EventLogStorage):
        assert storage
        if not storage.supports_global_concurrency_limits:
            pytest.skip("storage does not support global op concurrency")

        if self.can_wipe():
            storage.wipe()

        run_id = make_new_run_id()

        # initially there are no concurrency limited keys
        assert storage.get_concurrency_keys() == set()

        # set concurrency slot to 0
        storage.set_concurrency_slots("foo", 0)

        assert storage.get_concurrency_keys() == set(["foo"])
        info = storage.get_concurrency_info("foo")
        assert info.slot_count == 0
        assert info.active_slot_count == 0
        assert info.pending_step_count == 0
        assert info.assigned_step_count == 0

        # try claiming a slot
        claim_status = storage.claim_concurrency_slot("foo", run_id, "a")
        assert claim_status.slot_status == ConcurrencySlotStatus.BLOCKED
        info = storage.get_concurrency_info("foo")
        assert info.slot_count == 0
        assert info.active_slot_count == 0
        assert info.pending_step_count == 1
        assert info.assigned_step_count == 0

        # delete the concurrency slot
        storage.delete_concurrency_limit("foo")
        assert storage.get_concurrency_keys() == set()

    def test_default_concurrency(
        self,
        storage: EventLogStorage,
        instance: DagsterInstance,
    ):
        assert storage
        if not storage.supports_global_concurrency_limits:
            pytest.skip("storage does not support global op concurrency")

        if not self.can_set_concurrency_defaults():
            pytest.skip("storage does not support setting global op concurrency defaults")

        if self.can_wipe():
            storage.wipe()

        self.set_default_op_concurrency(instance, storage, 1)

        # initially there are no concurrency limited keys
        assert storage.get_concurrency_keys() == set()

        # initialize with default concurrency
        assert storage.initialize_concurrency_limit_to_default("foo")

        # initially there are no concurrency limited keys
        assert storage.get_concurrency_keys() == set(["foo"])
        assert storage.get_concurrency_info("foo").slot_count == 1

    def test_asset_checks(
        self,
        storage: EventLogStorage,
    ):
        if self.can_wipe():
            storage.wipe()

        check_key_1 = AssetCheckKey(AssetKey(["my_asset"]), "my_check")
        check_key_2 = AssetCheckKey(AssetKey(["my_asset"]), "my_check_2")

        storage.store_event(
            EventLogEntry(
                error_info=None,
                user_message="",
                level="debug",
                run_id="foo",
                timestamp=time.time(),
                dagster_event=DagsterEvent(
                    DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED.value,
                    "nonce",
                    event_specific_data=AssetCheckEvaluationPlanned(
                        asset_key=AssetKey(["my_asset"]), check_name="my_check"
                    ),
                ),
            )
        )

        checks = storage.get_asset_check_execution_history(check_key_1, limit=10)
        assert len(checks) == 1
        assert checks[0].status == AssetCheckExecutionRecordStatus.PLANNED
        assert checks[0].run_id == "foo"
        assert checks[0].event
        assert checks[0].event.dagster_event_type == DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED

        latest_checks = storage.get_latest_asset_check_execution_by_key([check_key_1, check_key_2])
        assert len(latest_checks) == 1
        assert latest_checks[check_key_1].status == AssetCheckExecutionRecordStatus.PLANNED
        assert latest_checks[check_key_1].run_id == "foo"

        # update the planned check
        storage.store_event(
            EventLogEntry(
                error_info=None,
                user_message="",
                level="debug",
                run_id="foo",
                timestamp=time.time(),
                dagster_event=DagsterEvent(
                    DagsterEventType.ASSET_CHECK_EVALUATION.value,
                    "nonce",
                    event_specific_data=AssetCheckEvaluation(
                        asset_key=AssetKey(["my_asset"]),
                        check_name="my_check",
                        passed=True,
                        metadata={},
                        target_materialization_data=AssetCheckEvaluationTargetMaterializationData(
                            storage_id=42, run_id="bizbuz", timestamp=3.3
                        ),
                        severity=AssetCheckSeverity.ERROR,
                    ),
                ),
            )
        )

        checks = storage.get_asset_check_execution_history(check_key_1, limit=10)
        assert len(checks) == 1
        assert checks[0].status == AssetCheckExecutionRecordStatus.SUCCEEDED
        assert checks[0].event
        assert checks[0].event.dagster_event
        check_data = checks[0].event.dagster_event.asset_check_evaluation_data
        assert check_data.target_materialization_data
        assert check_data.target_materialization_data.storage_id == 42

        latest_checks = storage.get_latest_asset_check_execution_by_key([check_key_1, check_key_2])
        assert len(latest_checks) == 1
        check = latest_checks[check_key_1]
        assert check.status == AssetCheckExecutionRecordStatus.SUCCEEDED
        assert check.event
        assert check.event.dagster_event
        check_data = check.event.dagster_event.asset_check_evaluation_data
        assert check_data.target_materialization_data
        assert check_data.target_materialization_data.storage_id == 42

        storage.store_event(
            EventLogEntry(
                error_info=None,
                user_message="",
                level="debug",
                run_id="foobar",
                timestamp=time.time(),
                dagster_event=DagsterEvent(
                    DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED.value,
                    "nonce",
                    event_specific_data=AssetCheckEvaluationPlanned(
                        asset_key=AssetKey(["my_asset"]), check_name="my_check"
                    ),
                ),
            )
        )

        checks = storage.get_asset_check_execution_history(check_key_1, limit=10)
        assert len(checks) == 2
        assert checks[0].status == AssetCheckExecutionRecordStatus.PLANNED
        assert checks[0].run_id == "foobar"
        assert checks[1].status == AssetCheckExecutionRecordStatus.SUCCEEDED
        assert checks[1].run_id == "foo"

        checks = storage.get_asset_check_execution_history(check_key_1, limit=1)
        assert len(checks) == 1
        assert checks[0].run_id == "foobar"

        checks = storage.get_asset_check_execution_history(
            check_key_1, limit=1, cursor=checks[0].id
        )
        assert len(checks) == 1
        assert checks[0].run_id == "foo"

        latest_checks = storage.get_latest_asset_check_execution_by_key([check_key_1, check_key_2])
        assert len(latest_checks) == 1
        assert latest_checks[check_key_1].status == AssetCheckExecutionRecordStatus.PLANNED
        assert latest_checks[check_key_1].run_id == "foobar"

        storage.store_event(
            EventLogEntry(
                error_info=None,
                user_message="",
                level="debug",
                run_id="fizbuz",
                timestamp=time.time(),
                dagster_event=DagsterEvent(
                    DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED.value,
                    "nonce",
                    event_specific_data=AssetCheckEvaluationPlanned(
                        asset_key=AssetKey(["my_asset"]), check_name="my_check_2"
                    ),
                ),
            )
        )

        latest_checks = storage.get_latest_asset_check_execution_by_key([check_key_1, check_key_2])
        assert len(latest_checks) == 2
        assert latest_checks[check_key_1].status == AssetCheckExecutionRecordStatus.PLANNED
        assert latest_checks[check_key_1].run_id == "foobar"
        assert latest_checks[check_key_2].status == AssetCheckExecutionRecordStatus.PLANNED
        assert latest_checks[check_key_2].run_id == "fizbuz"

    def test_external_asset_event(
        self,
        storage: EventLogStorage,
    ):
        key = AssetKey("test_asset")
        log_entry = EventLogEntry(
            error_info=None,
            user_message="",
            level="debug",
            run_id=RUNLESS_RUN_ID,
            timestamp=time.time(),
            dagster_event=DagsterEvent(
                event_type_value=DagsterEventType.ASSET_MATERIALIZATION.value,
                job_name=RUNLESS_JOB_NAME,
                event_specific_data=StepMaterializationData(
                    materialization=AssetMaterialization(asset_key=key, metadata={"was": "here"})
                ),
            ),
        )

        storage.store_event(log_entry)

        mats = storage.get_latest_materialization_events([key])
        assert mats
        mat = mats[key]
        assert mat
        assert mat.asset_materialization
        assert mat.asset_materialization.metadata["was"].value == "here"

    def test_large_asset_metadata(
        self,
        storage: EventLogStorage,
        test_run_id: str,
    ):
        key = AssetKey("test_asset")

        large_metadata = {
            f"key_{i}": "".join(random.choices(string.ascii_uppercase, k=1000)) for i in range(300)
        }
        storage.store_event(
            EventLogEntry(
                error_info=None,
                user_message="",
                level="debug",
                run_id=test_run_id,
                timestamp=time.time(),
                dagster_event=DagsterEvent(
                    event_type_value=DagsterEventType.ASSET_MATERIALIZATION.value,
                    job_name=RUNLESS_JOB_NAME,
                    event_specific_data=StepMaterializationData(
                        materialization=AssetMaterialization(asset_key=key, metadata=large_metadata)
                    ),
                ),
            )
        )

    def test_transaction(
        self,
        test_run_id: str,
        storage: EventLogStorage,
    ):
        if not isinstance(storage, SqlEventLogStorage):
            pytest.skip("This test is for SQL-backed Event Log behavior")

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

        class BlowUp(Exception):
            ...

        # now try to delete
        with pytest.raises(BlowUp):
            with storage.index_transaction() as conn:
                conn.execute(SqlEventLogStorageTable.delete())
                # Invalid insert, which should rollback the entire transaction
                raise BlowUp()

        assert len(storage.get_logs_for_run(test_run_id)) == 1

        if self.can_wipe():
            storage.wipe()
            assert len(storage.get_logs_for_run(test_run_id)) == 0
