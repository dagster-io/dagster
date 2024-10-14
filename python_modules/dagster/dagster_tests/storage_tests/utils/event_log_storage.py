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
import pytest
import sqlalchemy as db
from dagster import (
    AssetKey,
    AssetMaterialization,
    AssetObservation,
    AssetRecordsFilter,
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
from dagster._core.definitions.data_version import (
    _OLD_DATA_VERSION_TAG,
    _OLD_INPUT_DATA_VERSION_TAG_PREFIX,
    CODE_VERSION_TAG,
    DATA_VERSION_IS_USER_PROVIDED_TAG,
    DATA_VERSION_TAG,
    INPUT_DATA_VERSION_TAG_PREFIX,
    INPUT_EVENT_POINTER_TAG_PREFIX,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.dependency import NodeHandle
from dagster._core.definitions.job_base import InMemoryJob
from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionKey
from dagster._core.definitions.partition import PartitionKeyRange, StaticPartitionsDefinition
from dagster._core.definitions.time_window_partitions import (
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
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
from dagster._core.instance import RUNLESS_JOB_NAME, RUNLESS_RUN_ID
from dagster._core.loader import LoadingContext
from dagster._core.remote_representation.external_data import PartitionsSnap
from dagster._core.remote_representation.origin import (
    InProcessCodeLocationOrigin,
    RemoteJobOrigin,
    RemoteRepositoryOrigin,
)
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionRecordStatus
from dagster._core.storage.event_log import InMemoryEventLogStorage, SqlEventLogStorage
from dagster._core.storage.event_log.base import EventLogStorage
from dagster._core.storage.event_log.migration import (
    EVENT_LOG_DATA_MIGRATIONS,
    migrate_asset_key_data,
)
from dagster._core.storage.event_log.schema import SqlEventLogStorageTable
from dagster._core.storage.event_log.sqlite.sqlite_event_log import SqliteEventLogStorage
from dagster._core.storage.io_manager import IOManager
from dagster._core.storage.partition_status_cache import AssetStatusCacheValue
from dagster._core.storage.sqlalchemy_compat import db_select
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
    MULTIDIMENSIONAL_PARTITION_PREFIX,
)
from dagster._core.test_utils import create_run_for_test, instance_for_test
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.utils import make_new_run_id
from dagster._loggers import colored_console_logger
from dagster._serdes.serdes import deserialize_value
from dagster._time import get_current_datetime
from dagster._utils.concurrency import ConcurrencySlotStatus

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
                remote_job_origin=RemoteJobOrigin(
                    RemoteRepositoryOrigin(
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
    ops_fn_or_assets, run_id=None, check_success=True, instance=None, run_config=None, tags=None
) -> Tuple[List[EventLogEntry], JobExecutionResult]:
    events = []

    def _append_event(event):
        events.append(event)

    if isinstance(ops_fn_or_assets, list):  # assets
        job_def = Definitions(
            assets=ops_fn_or_assets,
            loggers=_default_loggers(_append_event),
            resources=_default_resources(),
            executor=in_process_executor,
        ).get_implicit_job_def_for_assets([k for a in ops_fn_or_assets for k in a.keys])
        assert job_def
        a_job = job_def
    else:  # op_fn

        @job(
            resource_defs=_default_resources(),
            logger_defs=_default_loggers(_append_event),
            executor_def=in_process_executor,
        )
        def a_job():
            ops_fn_or_assets()

    result = None

    with ExitStack() as stack:
        if not instance:
            instance = stack.enter_context(DagsterInstance.ephemeral())

        run_config = {
            **{"loggers": {"callback": {}, "console": {}}},
            **(run_config if run_config else {}),
        }

        dagster_run = instance.create_run_for_job(
            a_job, run_id=run_id, run_config=run_config, tags=tags
        )
        result = execute_run(InMemoryJob(a_job), dagster_run, instance)

        if check_success:
            assert result.success

    assert result

    return events, result


def _synthesize_and_store_events(storage, ops_fn, run_id, instance=None):
    events, _ = _synthesize_events(ops_fn, run_id, instance=instance)
    for event in events:
        storage.store_event(event)


def _store_materialization_events(storage, ops_fn, instance, run_id):
    _synthesize_and_store_events(storage, ops_fn, run_id, instance=instance)
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
    yield get_current_datetime()
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
        assert storage.get_logs_for_run(make_new_run_id()) == []

    def can_wipe_event_log(self):
        # Whether the storage is allowed to wipe the entire event log
        return True

    def can_query_all_asset_records(self):
        return True

    def can_write_cached_status(self):
        return True

    def can_watch(self):
        # Whether the storage is allowed to watch the event log
        return True

    def has_asset_partitions_table(self) -> bool:
        return False

    def can_set_concurrency_defaults(self):
        return False

    def supports_offset_cursor_queries(self):
        return True

    def supports_multiple_event_type_queries(self):
        return True

    def set_default_op_concurrency(self, instance, storage, limit):
        pass

    def watch_timeout(self):
        return 5

    @contextmanager
    def mock_tags_to_index(self, storage):
        passthrough_all_tags = lambda tags: tags
        with mock.patch.object(storage, "get_asset_tags_to_index", passthrough_all_tags):
            yield

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

        if self.can_wipe_event_log():
            storage.wipe()
            assert len(storage.get_logs_for_run(test_run_id)) == 0

    def test_event_log_storage_store_with_multiple_runs(
        self,
        instance: DagsterInstance,
        storage: EventLogStorage,
    ):
        runs = [make_new_run_id() for _ in range(3)]
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

        if self.can_wipe_event_log():
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

    def test_event_log_storage_storage_id_pagination(
        self,
        test_run_id: str,
        instance: DagsterInstance,
        storage: EventLogStorage,
    ):
        other_run_id = make_new_run_id()
        with create_and_delete_test_runs(instance, [other_run_id]):
            # two runs events to ensure pagination is not affected by other runs
            storage.store_event(create_test_event_log_record("A", run_id=test_run_id))
            storage.store_event(create_test_event_log_record(str(0), run_id=other_run_id))
            storage.store_event(create_test_event_log_record("B", run_id=test_run_id))
            storage.store_event(create_test_event_log_record(str(1), run_id=other_run_id))
            storage.store_event(create_test_event_log_record("C", run_id=test_run_id))
            storage.store_event(create_test_event_log_record(str(2), run_id=other_run_id))
            storage.store_event(create_test_event_log_record("D", run_id=test_run_id))

            desc_result = storage.get_records_for_run(test_run_id, ascending=False)
            assert [r.event_log_entry.user_message for r in desc_result.records] == [
                "D",
                "C",
                "B",
                "A",
            ]

            asc_result = storage.get_records_for_run(test_run_id, ascending=True)
            assert [r.event_log_entry.user_message for r in asc_result.records] == [
                "A",
                "B",
                "C",
                "D",
            ]

            storage_ids = [r.storage_id for r in asc_result.records]
            assert len(storage_ids) == 4

            def _cursor(storage_id: int):
                return EventLogCursor.from_storage_id(storage_id).to_string()

            assert len(storage.get_logs_for_run(test_run_id)) == 4
            assert len(storage.get_logs_for_run(test_run_id, _cursor(storage_ids[0]))) == 3
            assert len(storage.get_logs_for_run(test_run_id, _cursor(storage_ids[1]))) == 2
            assert len(storage.get_logs_for_run(test_run_id, _cursor(storage_ids[2]))) == 1
            assert len(storage.get_logs_for_run(test_run_id, _cursor(storage_ids[3]))) == 0

    def test_event_log_storage_offset_pagination(
        self,
        test_run_id: str,
        instance: DagsterInstance,
        storage: EventLogStorage,
    ):
        if not self.supports_offset_cursor_queries():
            pytest.skip("storage does not support deprecated offset cursor queries")

        other_run_id = make_new_run_id()
        with create_and_delete_test_runs(instance, [other_run_id]):
            # two runs events to ensure pagination is not affected by other runs
            storage.store_event(create_test_event_log_record("A", run_id=test_run_id))
            storage.store_event(create_test_event_log_record(str(0), run_id=other_run_id))
            storage.store_event(create_test_event_log_record("B", run_id=test_run_id))
            storage.store_event(create_test_event_log_record(str(1), run_id=other_run_id))
            storage.store_event(create_test_event_log_record("C", run_id=test_run_id))
            storage.store_event(create_test_event_log_record(str(2), run_id=other_run_id))
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

        event_records = storage.get_records_for_run(result.run_id, ascending=True).records
        storage_ids = [r.storage_id for r in event_records]

        out_events = []
        offset = -1
        fuse = 0
        chunk_size = 2
        while fuse < 50:
            fuse += 1
            # fetch in batches w/ limit & cursor
            cursor = (
                EventLogCursor.from_storage_id(storage_ids[offset]).to_string()
                if offset >= 0
                else None
            )
            chunk = storage.get_logs_for_run(result.run_id, cursor=cursor, limit=chunk_size)
            if not chunk:
                break
            assert len(chunk) <= chunk_size
            out_events += chunk
            offset += len(chunk)

        assert _event_types(out_events) == _event_types(events)

    def test_get_logs_for_run_cursor_offset_limit(self, test_run_id, storage):
        if not self.supports_offset_cursor_queries():
            pytest.skip("storage does not support deprecated offset cursor queries")

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

        if self.can_wipe_event_log():
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
        while len(event_list) < len(events) and time.time() - start < self.watch_timeout():
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
            while len(event_list) < len(events_two) and time.time() - start < self.watch_timeout():
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
            ) and time.time() - start < self.watch_timeout():
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

    def test_asset_materialization(self, storage, instance):
        asset_key = AssetKey(["path", "to", "asset_one"])

        test_run_id = make_new_run_id()

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

        _synthesize_events(_ops, instance=instance, run_id=test_run_id)

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

    def test_asset_materialization_range(self, storage, test_run_id):
        partitions_def = StaticPartitionsDefinition(["a", "b"])

        class DummyIOManager(IOManager):
            def handle_output(self, context, obj):
                pass

            def load_input(self, context):
                return 1

        @asset(partitions_def=partitions_def, io_manager_def=DummyIOManager())
        def foo():
            return {"a": 1, "b": 2}

        with instance_for_test() as test_instance:
            events, _ = _synthesize_events(
                [foo],
                instance=test_instance,
                run_id=test_run_id,
                tags={ASSET_PARTITION_RANGE_START_TAG: "a", ASSET_PARTITION_RANGE_END_TAG: "b"},
            )

        materializations = [
            e for e in events if e.dagster_event.event_type == "ASSET_MATERIALIZATION"
        ]
        storage.store_event_batch(materializations)

        result = storage.fetch_materializations(foo.key, limit=100)
        assert len(result.records) == 2

    def test_asset_materialization_fetch(self, storage, instance):
        asset_key = AssetKey(["path", "to", "asset_one"])

        other_asset_key = AssetKey(["path", "to", "asset_two"])

        test_run_id = make_new_run_id()

        @op
        def materialize(_):
            yield AssetMaterialization(asset_key=asset_key, metadata={"count": 1}, partition="1")
            yield AssetMaterialization(asset_key=asset_key, metadata={"count": 2}, partition="2")
            yield AssetMaterialization(asset_key=asset_key, metadata={"count": 3}, partition="3")
            yield AssetMaterialization(asset_key=asset_key, metadata={"count": 4}, partition="4")
            yield AssetMaterialization(asset_key=asset_key, metadata={"count": 5}, partition="5")
            yield AssetMaterialization(
                asset_key=other_asset_key, metadata={"count": 1}, partition="z"
            )

            yield AssetMaterialization(
                asset_key=asset_key, metadata={"count": 1}, partition="dupe_materialization"
            )
            yield AssetMaterialization(
                asset_key=asset_key, metadata={"count": 2}, partition="dupe_materialization"
            )

            yield Output(1)

        def _ops():
            materialize()

        _synthesize_events(_ops, instance=instance, run_id=test_run_id)

        assert asset_key in set(storage.all_asset_keys())

        def _get_counts(result):
            assert isinstance(result, EventRecordsResult)
            return [
                record.asset_materialization.metadata.get("count").value
                for record in result.records
            ]

        # results come in descending order, by default
        result = storage.fetch_materializations(asset_key, limit=100)
        assert _get_counts(result) == [2, 1, 5, 4, 3, 2, 1]

        result = storage.fetch_materializations(asset_key, limit=3)
        assert _get_counts(result) == [2, 1, 5]

        # results come in ascending order, limited
        result = storage.fetch_materializations(asset_key, limit=3, ascending=True)
        assert _get_counts(result) == [1, 2, 3]

        storage_id_3 = result.records[2].storage_id
        timestamp_3 = result.records[2].timestamp
        storage_id_1 = result.records[0].storage_id
        timestamp_1 = result.records[0].timestamp

        other_key_result = storage.fetch_materializations(other_asset_key, limit=1, ascending=True)
        other_key_storage_id = other_key_result.records[0].storage_id

        # filter by after storage id
        result = storage.fetch_materializations(
            AssetRecordsFilter(
                asset_key=asset_key,
                after_storage_id=storage_id_1,
            ),
            limit=100,
        )
        assert _get_counts(result) == [2, 1, 5, 4, 3, 2]

        # filter by before storage id
        result = storage.fetch_materializations(
            AssetRecordsFilter(
                asset_key=asset_key,
                before_storage_id=storage_id_3,
            ),
            limit=100,
        )
        assert _get_counts(result) == [2, 1]

        # filter by before and after storage id
        result = storage.fetch_materializations(
            AssetRecordsFilter(
                asset_key=asset_key,
                before_storage_id=storage_id_3,
                after_storage_id=storage_id_1,
            ),
            limit=100,
        )
        assert _get_counts(result) == [2]

        # filter by timestamp
        result = storage.fetch_materializations(
            AssetRecordsFilter(
                asset_key=asset_key,
                before_timestamp=timestamp_3,
            ),
            limit=100,
        )
        assert _get_counts(result) == [2, 1]

        # filter by before and after timestamp
        result = storage.fetch_materializations(
            AssetRecordsFilter(
                asset_key=asset_key,
                before_timestamp=timestamp_3,
                after_timestamp=timestamp_1,
            ),
            limit=100,
        )
        assert _get_counts(result) == [2]

        # filter by storage ids
        result = storage.fetch_materializations(
            AssetRecordsFilter(
                asset_key=asset_key,
                storage_ids=[storage_id_1, storage_id_3, other_key_storage_id],
            ),
            limit=100,
        )
        assert _get_counts(result) == [3, 1]

        # filter by partitions
        result = storage.fetch_materializations(
            AssetRecordsFilter(
                asset_key=asset_key,
                asset_partitions=["1", "3", "5"],
            ),
            limit=100,
        )
        assert _get_counts(result) == [5, 3, 1]

        # fetch most recent event for a given partition
        result = storage.fetch_materializations(
            AssetRecordsFilter(
                asset_key=asset_key,
                asset_partitions=["dupe_materialization"],
            ),
            limit=1,
        )
        assert _get_counts(result) == [2]

        result = storage.fetch_materializations(
            AssetRecordsFilter(
                asset_key=asset_key,
                asset_partitions=["5"],
            ),
            limit=1,
        )
        assert _get_counts(result) == [5]

        result = storage.fetch_materializations(
            AssetRecordsFilter(
                asset_key=asset_key,
                asset_partitions=["non_existant"],
            ),
            limit=1,
        )
        assert _get_counts(result) == []

    def test_asset_observation_fetch(self, storage, instance):
        asset_key = AssetKey(["path", "to", "asset_one"])

        test_run_id = make_new_run_id()

        @op
        def observe(_):
            yield AssetObservation(asset_key=asset_key, metadata={"count": 1}, partition="1")
            yield AssetObservation(asset_key=asset_key, metadata={"count": 2}, partition="2")
            yield AssetObservation(asset_key=asset_key, metadata={"count": 3}, partition="3")
            yield AssetObservation(asset_key=asset_key, metadata={"count": 4}, partition="4")
            yield AssetObservation(asset_key=asset_key, metadata={"count": 5}, partition="5")

            yield AssetObservation(
                asset_key=asset_key, metadata={"count": 1}, partition="dupe_observation"
            )
            yield AssetObservation(
                asset_key=asset_key, metadata={"count": 2}, partition="dupe_observation"
            )

            yield Output(1)

        def _ops():
            observe()

        _synthesize_events(_ops, instance=instance, run_id=test_run_id)

        assert asset_key in set(storage.all_asset_keys())

        def _get_counts(result):
            assert isinstance(result, EventRecordsResult)
            return [
                record.asset_observation.metadata.get("count").value for record in result.records
            ]

        # results come in descending order, by default
        result = storage.fetch_observations(asset_key, limit=100)
        assert _get_counts(result) == [2, 1, 5, 4, 3, 2, 1]

        result = storage.fetch_observations(asset_key, limit=3)
        assert _get_counts(result) == [2, 1, 5]

        # results come in ascending order, limited
        result = storage.fetch_observations(asset_key, limit=3, ascending=True)
        assert _get_counts(result) == [1, 2, 3]

        storage_id_3 = result.records[2].storage_id
        timestamp_3 = result.records[2].timestamp
        storage_id_1 = result.records[0].storage_id
        timestamp_1 = result.records[0].timestamp

        # filter by after storage id
        result = storage.fetch_observations(
            AssetRecordsFilter(
                asset_key=asset_key,
                after_storage_id=storage_id_1,
            ),
            limit=100,
        )
        assert _get_counts(result) == [2, 1, 5, 4, 3, 2]

        # filter by before storage id
        result = storage.fetch_observations(
            AssetRecordsFilter(
                asset_key=asset_key,
                before_storage_id=storage_id_3,
            ),
            limit=100,
        )
        assert _get_counts(result) == [2, 1]

        # filter by before and after storage id
        result = storage.fetch_observations(
            AssetRecordsFilter(
                asset_key=asset_key,
                before_storage_id=storage_id_3,
                after_storage_id=storage_id_1,
            ),
            limit=100,
        )
        assert _get_counts(result) == [2]

        # filter by timestamp
        result = storage.fetch_observations(
            AssetRecordsFilter(
                asset_key=asset_key,
                before_timestamp=timestamp_3,
            ),
            limit=100,
        )
        assert _get_counts(result) == [2, 1]

        # filter by before and after timestamp
        result = storage.fetch_observations(
            AssetRecordsFilter(
                asset_key=asset_key,
                before_timestamp=timestamp_3,
                after_timestamp=timestamp_1,
            ),
            limit=100,
        )
        assert _get_counts(result) == [2]

        # filter by storage ids
        result = storage.fetch_observations(
            AssetRecordsFilter(
                asset_key=asset_key,
                storage_ids=[storage_id_1, storage_id_3],
            ),
            limit=100,
        )
        assert _get_counts(result) == [3, 1]

        # filter by partitions
        result = storage.fetch_observations(
            AssetRecordsFilter(
                asset_key=asset_key,
                asset_partitions=["1", "3", "5"],
            ),
            limit=100,
        )
        assert _get_counts(result) == [5, 3, 1]

        # fetch most recent event for a given partition
        result = storage.fetch_observations(
            AssetRecordsFilter(
                asset_key=asset_key,
                asset_partitions=["dupe_observation"],
            ),
            limit=1,
        )
        assert _get_counts(result) == [2]

        result = storage.fetch_observations(
            AssetRecordsFilter(
                asset_key=asset_key,
                asset_partitions=["5"],
            ),
            limit=1,
        )
        assert _get_counts(result) == [5]

        result = storage.fetch_observations(
            AssetRecordsFilter(
                asset_key=asset_key,
                asset_partitions=["non_existant"],
            ),
            limit=1,
        )
        assert _get_counts(result) == []

    def test_asset_materialization_null_key_fails(self):
        with pytest.raises(check.CheckError):
            AssetMaterialization(asset_key=None)

    def test_asset_events_error_parsing(self, storage, instance):
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

        _synthesize_events(_ops, instance=instance)

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

            def _get_storage_ids(result):
                return [record.storage_id for record in result.records]

            result = storage.fetch_run_status_changes(DagsterEventType.RUN_SUCCESS, limit=100)
            assert len(result.records) == 3
            assert set(_event_types([r.event_log_entry for r in result.records])) == {
                DagsterEventType.RUN_SUCCESS
            }

            # default is descending order
            assert result.records[0].storage_id > result.records[2].storage_id
            storage_id_3, storage_id_2, storage_id_1 = [
                event.storage_id for event in result.records
            ]
            timestamp_3, timestamp_2, timestamp_1 = [event.timestamp for event in result.records]

            # apply a limit
            result = storage.fetch_run_status_changes(DagsterEventType.RUN_SUCCESS, limit=2)
            assert _get_storage_ids(result) == [storage_id_3, storage_id_2]

            # results come in ascending order, limited
            result = storage.fetch_run_status_changes(
                DagsterEventType.RUN_SUCCESS, limit=2, ascending=True
            )
            assert _get_storage_ids(result) == [storage_id_1, storage_id_2]

            # use storage id for cursor
            cursor = EventLogCursor.from_storage_id(storage_id_2).to_string()
            result = storage.fetch_run_status_changes(
                DagsterEventType.RUN_SUCCESS, cursor=cursor, limit=100
            )
            assert _get_storage_ids(result) == [storage_id_1]

            # use storage id for cursor, ascending
            cursor = EventLogCursor.from_storage_id(storage_id_2).to_string()
            result = storage.fetch_run_status_changes(
                DagsterEventType.RUN_SUCCESS, cursor=cursor, ascending=True, limit=100
            )
            assert _get_storage_ids(result) == [storage_id_3]

            # filter by after storage id
            result = storage.fetch_run_status_changes(
                RunStatusChangeRecordsFilter(
                    DagsterEventType.RUN_SUCCESS, after_storage_id=storage_id_1
                ),
                limit=100,
            )
            assert _get_storage_ids(result) == [storage_id_3, storage_id_2]

            # filter by before storage id
            result = storage.fetch_run_status_changes(
                RunStatusChangeRecordsFilter(
                    DagsterEventType.RUN_SUCCESS, before_storage_id=storage_id_3
                ),
                limit=100,
            )
            assert _get_storage_ids(result) == [storage_id_2, storage_id_1]

            # filter by before and after storage id
            result = storage.fetch_run_status_changes(
                RunStatusChangeRecordsFilter(
                    DagsterEventType.RUN_SUCCESS,
                    after_storage_id=storage_id_1,
                    before_storage_id=storage_id_3,
                ),
                limit=100,
            )
            assert _get_storage_ids(result) == [storage_id_2]

            # filter by after timestamp
            result = storage.fetch_run_status_changes(
                RunStatusChangeRecordsFilter(
                    DagsterEventType.RUN_SUCCESS, after_timestamp=timestamp_1
                ),
                limit=100,
            )
            assert _get_storage_ids(result) == [storage_id_3, storage_id_2]

            # filter by before timestamp
            result = storage.fetch_run_status_changes(
                RunStatusChangeRecordsFilter(
                    DagsterEventType.RUN_SUCCESS, before_timestamp=timestamp_3
                ),
                limit=100,
            )
            assert _get_storage_ids(result) == [storage_id_2, storage_id_1]

            # filter by before and after timestamp
            result = storage.fetch_run_status_changes(
                RunStatusChangeRecordsFilter(
                    DagsterEventType.RUN_SUCCESS,
                    after_timestamp=timestamp_1,
                    before_timestamp=timestamp_3,
                ),
                limit=100,
            )
            assert _get_storage_ids(result) == [storage_id_2]

            result = storage.fetch_run_status_changes(
                RunStatusChangeRecordsFilter(
                    DagsterEventType.RUN_SUCCESS, storage_ids=[storage_id_1, storage_id_3]
                ),
                limit=100,
            )
            assert _get_storage_ids(result) == [storage_id_3, storage_id_1]

    def test_get_event_records_sqlite(self, storage, instance):
        if not self.is_sqlite(storage):
            pytest.skip()

        asset_key = AssetKey(["path", "to", "asset_one"])
        run_id_1, run_id_2, run_id_3 = [make_new_run_id() for _ in range(3)]

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

        instance.wipe()

        # first run
        execute_run(
            InMemoryJob(a_job),
            instance.create_run_for_job(
                a_job,
                run_id=run_id_1,
                run_config={"loggers": {"callback": {}, "console": {}}},
            ),
            instance,
        )

        run_records = instance.get_run_records()
        assert len(run_records) == 1

        # second run
        events = []
        execute_run(
            InMemoryJob(a_job),
            instance.create_run_for_job(
                a_job,
                run_id=run_id_2,
                run_config={"loggers": {"callback": {}, "console": {}}},
            ),
            instance,
        )
        run_records = instance.get_run_records()
        assert len(run_records) == 2

        # third run
        events = []
        execute_run(
            InMemoryJob(a_job),
            instance.create_run_for_job(
                a_job,
                run_id=run_id_3,
                run_config={"loggers": {"callback": {}, "console": {}}},
            ),
            instance,
        )
        run_records = instance.get_run_records()
        assert len(run_records) == 3

        update_timestamp = run_records[-1].update_timestamp

        # use tz-aware cursor
        filtered_records = storage.get_event_records(
            EventRecordsFilter(
                event_type=DagsterEventType.RUN_SUCCESS,
                after_cursor=RunShardedEventsCursor(
                    id=0, run_updated_after=update_timestamp
                ),  # events after first run
            ),
            ascending=True,
        )

        assert len(filtered_records) == 2
        assert _event_types([r.event_log_entry for r in filtered_records]) == [
            DagsterEventType.RUN_SUCCESS,
            DagsterEventType.RUN_SUCCESS,
        ]
        assert [r.event_log_entry.run_id for r in filtered_records] == [run_id_2, run_id_3]

        # use tz-naive cursor
        filtered_records = storage.get_event_records(
            EventRecordsFilter(
                event_type=DagsterEventType.RUN_SUCCESS,
                after_cursor=RunShardedEventsCursor(
                    id=0, run_updated_after=update_timestamp.replace(tzinfo=None)
                ),  # events after first run
            ),
            ascending=True,
        )
        assert len(filtered_records) == 2
        assert _event_types([r.event_log_entry for r in filtered_records]) == [
            DagsterEventType.RUN_SUCCESS,
            DagsterEventType.RUN_SUCCESS,
        ]
        assert [r.event_log_entry.run_id for r in filtered_records] == [run_id_2, run_id_3]

        # use invalid cursor
        with pytest.raises(Exception, match="Add a RunShardedEventsCursor to your query filter"):
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
        while len(event_list) < len(safe_events) and time.time() - start < self.watch_timeout():
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
        while len(event_list) < len(safe_events) and time.time() - start < self.watch_timeout():
            time.sleep(0.01)

        assert len(event_list) == len(safe_events)
        assert all([isinstance(event, EventLogEntry) for event in event_list])

    def test_engine_event_markers(self, storage, instance):
        @op
        def return_one(_):
            return 1

        @job
        def a_job():
            return_one()

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

    def test_asset_keys(self, storage, instance):
        _synthesize_events(lambda: one_asset_op(), instance=instance)
        _synthesize_events(lambda: two_asset_ops(), instance=instance)

        asset_keys = storage.all_asset_keys()
        assert len(asset_keys) == 3
        assert set([asset_key.to_string() for asset_key in asset_keys]) == set(
            ['["asset_1"]', '["asset_2"]', '["path", "to", "asset_3"]']
        )

    def test_has_asset_key(self, storage, instance):
        _synthesize_events(lambda: one_asset_op(), instance=instance)
        _synthesize_events(lambda: two_asset_ops(), instance=instance)

        assert storage.has_asset_key(AssetKey(["path", "to", "asset_3"]))
        assert not storage.has_asset_key(AssetKey(["path", "to", "bogus", "asset"]))

    def test_asset_normalization(self, storage, instance):
        test_run_id = make_new_run_id()

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
        one_run_id = make_new_run_id()
        two_run_id = make_new_run_id()
        _synthesize_events(lambda: one_asset_op(), run_id=one_run_id, instance=instance)
        _synthesize_events(lambda: two_asset_ops(), run_id=two_run_id, instance=instance)

        asset_keys = storage.all_asset_keys()
        assert len(asset_keys) == 3
        assert storage.has_asset_key(AssetKey("asset_1"))

        log_count = len(storage.get_logs_for_run(one_run_id))
        for asset_key in asset_keys:
            storage.wipe_asset(asset_key)

        asset_keys = storage.all_asset_keys()
        assert len(asset_keys) == 0
        assert not storage.has_asset_key(AssetKey("asset_1"))
        assert log_count == len(storage.get_logs_for_run(one_run_id))

        one_run_id = make_new_run_id()
        _synthesize_events(
            lambda: one_asset_op(),
            run_id=one_run_id,
            instance=instance,
        )
        asset_keys = storage.all_asset_keys()
        assert len(asset_keys) == 1
        assert storage.has_asset_key(AssetKey("asset_1"))

    def test_asset_secondary_index(self, storage, instance):
        _synthesize_events(lambda: one_asset_op(), instance=instance)

        asset_keys = storage.all_asset_keys()
        assert len(asset_keys) == 1
        migrate_asset_key_data(storage)

        two_first_run_id = make_new_run_id()
        two_second_run_id = make_new_run_id()
        _synthesize_events(
            lambda: two_asset_ops(),
            run_id=two_first_run_id,
            instance=instance,
        )
        _synthesize_events(
            lambda: two_asset_ops(),
            run_id=two_second_run_id,
            instance=instance,
        )

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

        get_partitioned_config = lambda partition: {
            "ops": {"op_partitioned": {"config": {"partition": partition}}}
        }

        partitions = ["a", "a", "b", "c"]
        run_ids = [make_new_run_id() for _ in partitions]
        for partition, run_id in zip([f"partition_{x}" for x in partitions], run_ids):
            _synthesize_events(
                lambda: op_partitioned(),
                instance=instance,
                run_config=get_partitioned_config(partition),
                run_id=run_id,
            )

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

    def test_get_asset_keys(self, storage, instance):
        test_run_id = make_new_run_id()

        @op
        def gen_op():
            yield AssetMaterialization(asset_key=AssetKey(["a"]))
            yield AssetMaterialization(asset_key=AssetKey(["c"]))
            yield AssetMaterialization(asset_key=AssetKey(["banana"]))
            yield AssetMaterialization(asset_key=AssetKey(["b", "x"]))
            yield AssetMaterialization(asset_key=AssetKey(["b", "y"]))
            yield AssetMaterialization(asset_key=AssetKey(["b", "z"]))
            yield Output(1)

        _synthesize_events(lambda: gen_op(), instance=instance, run_id=test_run_id)

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

        # pagination still works even if the key is not in the list
        asset_keys = storage.get_asset_keys(cursor='["b", "w"]', limit=1)
        assert len(asset_keys) == 1
        assert asset_keys[0].to_string() == '["b", "x"]'

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

        run_id_1 = make_new_run_id()
        run_id_2 = make_new_run_id()
        run_id_3 = make_new_run_id()
        run_id_4 = make_new_run_id()

        cursor_run1 = _store_materialization_events(storage, materialize, instance, run_id_1)
        assert storage.get_materialized_partitions(a) == set()
        assert storage.get_materialized_partitions(b) == set()
        assert storage.get_materialized_partitions(c) == {"a", "b"}

        cursor_run2 = _store_materialization_events(storage, materialize_two, instance, run_id_2)
        _store_materialization_events(storage, materialize_three, instance, run_id_3)

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
        storage.wipe_asset(c)
        assert storage.get_materialized_partitions(c) == set()

        _store_materialization_events(storage, materialize_two, instance, run_id_4)

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

        with self.mock_tags_to_index(storage), create_and_delete_test_runs(instance, [run_id]):
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

    @pytest.mark.parametrize(
        "dagster_event_type",
        [DagsterEventType.ASSET_OBSERVATION, DagsterEventType.ASSET_MATERIALIZATION],
    )
    def test_get_latest_data_version_by_partition(self, storage, instance, dagster_event_type):
        """Test that queries latest data version (same as above test, but without needing to mock the indexed tags)."""
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
                    a, dagster_event_type, tag_keys=[DATA_VERSION_TAG]
                )
                == {}
            )

            # p1 materialized
            _store_partition_event(a, "p1", tags={DATA_VERSION_TAG: "1"})

            # p2 materialized
            _store_partition_event(a, "p2", tags={DATA_VERSION_TAG: "1"})

            # unrelated asset materialized
            t1 = _store_partition_event(b, "p1", tags={DATA_VERSION_TAG: "..."})
            _store_partition_event(b, "p2", tags={DATA_VERSION_TAG: "..."})

            # p1 re materialized
            _store_partition_event(a, "p1", tags={DATA_VERSION_TAG: "2"})

            # p3 materialized
            _store_partition_event(a, "p3", tags={DATA_VERSION_TAG: "1"})

            # subset of existing tag keys
            assert storage.get_latest_tags_by_partition(
                a, dagster_event_type, tag_keys=[DATA_VERSION_TAG]
            ) == {
                "p1": {DATA_VERSION_TAG: "2"},
                "p2": {DATA_VERSION_TAG: "1"},
                "p3": {DATA_VERSION_TAG: "1"},
            }

            # subset of existing partition keys
            assert storage.get_latest_tags_by_partition(
                a,
                dagster_event_type,
                tag_keys=[DATA_VERSION_TAG],
                asset_partitions=["p1"],
            ) == {
                "p1": {DATA_VERSION_TAG: "2"},
            }

            # superset of existing partition keys
            assert storage.get_latest_tags_by_partition(
                a,
                dagster_event_type,
                tag_keys=[DATA_VERSION_TAG],
                asset_partitions=["p1", "p2", "p3", "p4"],
            ) == {
                "p1": {DATA_VERSION_TAG: "2"},
                "p2": {DATA_VERSION_TAG: "1"},
                "p3": {DATA_VERSION_TAG: "1"},
            }

            # before p1 rematerialized and p3 existed
            assert storage.get_latest_tags_by_partition(
                a,
                dagster_event_type,
                tag_keys=[DATA_VERSION_TAG],
                before_cursor=t1,
            ) == {
                "p1": {DATA_VERSION_TAG: "1"},
                "p2": {DATA_VERSION_TAG: "1"},
            }

            # shouldn't include p2's materialization
            assert storage.get_latest_tags_by_partition(
                a,
                dagster_event_type,
                tag_keys=[DATA_VERSION_TAG],
                after_cursor=t1,
            ) == {
                "p1": {DATA_VERSION_TAG: "2"},
                "p3": {DATA_VERSION_TAG: "1"},
            }

            storage.wipe_asset(a)
            assert (
                storage.get_latest_tags_by_partition(
                    a,
                    dagster_event_type,
                    tag_keys=[DATA_VERSION_TAG],
                )
                == {}
            )
            _store_partition_event(a, "p1", tags={DATA_VERSION_TAG: "3"})
            assert storage.get_latest_tags_by_partition(
                a, dagster_event_type, tag_keys=[DATA_VERSION_TAG]
            ) == {
                "p1": {DATA_VERSION_TAG: "3"},
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

    def test_get_latest_asset_partition_materialization_attempts_without_materializations_external_asset(
        self, storage, instance
    ):
        a = AssetKey(["a"])

        def _planned_unmaterialized_runs_by_partition(asset_key):
            result = storage.get_latest_asset_partition_materialization_attempts_without_materializations(
                asset_key
            )
            return {partition: run_id for partition, (run_id, _event_id) in result.items()}

        run_id = make_new_run_id()
        with create_and_delete_test_runs(instance, [run_id]):
            # no events
            assert _planned_unmaterialized_runs_by_partition(a) == {}

            storage.store_event(
                EventLogEntry(
                    error_info=None,
                    level="debug",
                    user_message="",
                    run_id=run_id,
                    timestamp=time.time(),
                    dagster_event=DagsterEvent(
                        DagsterEventType.ASSET_MATERIALIZATION_PLANNED.value,
                        "nonce",
                        event_specific_data=AssetMaterializationPlannedData(a, "foo"),
                    ),
                )
            )

            # new materialization planned appears
            assert _planned_unmaterialized_runs_by_partition(a) == {"foo": run_id}

            # materialize external asset
            storage.store_event(
                EventLogEntry(
                    error_info=None,
                    level="debug",
                    user_message="",
                    run_id=RUNLESS_RUN_ID,
                    timestamp=time.time(),
                    dagster_event=DagsterEvent(
                        DagsterEventType.ASSET_MATERIALIZATION.value,
                        RUNLESS_JOB_NAME,
                        event_specific_data=StepMaterializationData(
                            AssetMaterialization(asset_key=a, partition="foo")
                        ),
                    ),
                )
            )

            # no events
            assert _planned_unmaterialized_runs_by_partition(a) == {}

    def test_store_asset_materialization_planned_event_with_invalid_partitions_subset(
        self, storage, instance
    ) -> None:
        a = AssetKey(["a"])
        run_id_1 = make_new_run_id()

        partitions_def = DailyPartitionsDefinition("2023-01-01")
        partitions_subset = (
            PartitionsSnap.from_def(partitions_def)
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
            PartitionsSnap.from_def(partitions_def)
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
            PartitionsSnap.from_def(partitions_def)
            .get_partitions_definition()
            .subset_with_partition_keys(
                partitions_def.get_partition_keys_in_range(
                    PartitionKeyRange("2023-01-05", "2023-01-06")
                )
            )
            .to_serializable_subset()
        )

        _synthesize_events(lambda: gen_op(), instance=instance, run_id=gen_events_run_id)

        with create_and_delete_test_runs(instance, [subset_event_run_id]):
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

            single_partition_event_id = storage.get_latest_planned_materialization_info(
                asset_key=a
            ).storage_id

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

            partition_subset_event_id = storage.get_latest_planned_materialization_info(
                asset_key=a
            ).storage_id

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
                    partition_subset_event_id,
                )
                assert planned_but_no_materialization_partitions["2023-01-06"] == (
                    subset_event_run_id,
                    partition_subset_event_id,
                )

            else:
                # When an asset partitions table is not present we can only fetch planned but
                # not materialized partitions when planned events target a single partition
                assert planned_but_no_materialization_partitions.keys() == {"2023-01-05"}
                assert planned_but_no_materialization_partitions["2023-01-05"] == (
                    subset_event_run_id,
                    single_partition_event_id,
                )

                # When asset partitions table is not present get_latest_storage_id_by_partition
                # only returns storage IDs for single-partition events
                latest_storage_id_by_partition = storage.get_latest_storage_id_by_partition(
                    a, DagsterEventType.ASSET_MATERIALIZATION_PLANNED
                )
                assert latest_storage_id_by_partition == {"2023-01-05": single_partition_event_id}

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
            foo_event_id = storage.get_latest_planned_materialization_info(asset_key=a).storage_id
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
            bar_event_id = storage.get_latest_planned_materialization_info(asset_key=a).storage_id
            assert (
                storage.get_latest_asset_partition_materialization_attempts_without_materializations(
                    a
                )
                == {
                    "foo": (run_id_1, foo_event_id),
                    "bar": (run_id_2, bar_event_id),
                }
            )
            assert (
                storage.get_latest_asset_partition_materialization_attempts_without_materializations(
                    a, foo_event_id
                )
                == {
                    "bar": (run_id_2, bar_event_id),
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
                    "foo": (run_id_1, foo_event_id),
                    "bar": (run_id_3, bar_event_id + 1),
                }
            )

    def test_get_observation(self, storage: EventLogStorage, instance):
        a = AssetKey(["key_a"])

        test_run_id = make_new_run_id()

        @op
        def gen_op():
            yield AssetObservation(asset_key=a, metadata={"foo": "bar"})
            yield Output(1)

        _synthesize_events(lambda: gen_op(), instance=instance, run_id=test_run_id)

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

        # unpartitioned query
        unpartitioned_info = storage.get_latest_planned_materialization_info(asset_key=a)
        assert unpartitioned_info
        assert unpartitioned_info.run_id == test_run_id
        foo_storage_id = unpartitioned_info.storage_id

        # matching partitioned query
        foo_info = storage.get_latest_planned_materialization_info(asset_key=a, partition="foo")
        assert foo_info
        assert foo_info.run_id == test_run_id
        assert foo_info.storage_id == foo_storage_id

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

        # unpartitioned query
        unpartitioned_info = storage.get_latest_planned_materialization_info(asset_key=a)
        assert unpartitioned_info
        assert unpartitioned_info.run_id == test_run_id
        assert unpartitioned_info.storage_id != foo_storage_id
        bar_storage_id = unpartitioned_info.storage_id

        # foo partitioned query
        foo_info = storage.get_latest_planned_materialization_info(asset_key=a, partition="foo")
        assert foo_info
        assert foo_info.run_id == test_run_id
        assert foo_info.storage_id == foo_storage_id

        # bar partitioned query
        bar_info = storage.get_latest_planned_materialization_info(asset_key=a, partition="bar")
        assert bar_info
        assert bar_info.run_id == test_run_id
        assert bar_info.storage_id == bar_storage_id

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
        _synthesize_events(lambda: my_op(), instance=instance, run_id=run_id_1)

        assert [key] == storage.all_asset_keys()

        storage.wipe_asset(key)

        assert len(storage.all_asset_keys()) == 0

        events, _ = _synthesize_events(lambda: my_op(), instance=instance, run_id=run_id_2)
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

        test_run_id = make_new_run_id()

        _synthesize_events(lambda: gen_op(), instance=instance, run_id=test_run_id)

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

        my_asset_key = AssetKey("my_asset")
        # second_asset_key = AssetKey("second_asset")
        # storage.get_asset_records([my_asset_key, second_asset_key])

        assert len(storage.get_asset_records()) == 0

        run_id_1 = make_new_run_id()
        run_id_2 = make_new_run_id()
        defs = Definitions(
            assets=[my_asset, second_asset],
            jobs=[
                define_asset_job("one_asset_job", ["my_asset"]),
                define_asset_job("two_asset_job"),
            ],
        )
        result = _execute_job_and_store_events(
            instance,
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

        # get the materialization from the one_asset_job run
        event_log_record = storage.get_records_for_run(
            run_id_1,
            of_type=DagsterEventType.ASSET_MATERIALIZATION,
            limit=1,
            ascending=False,
        ).records[0]

        if self.is_sqlite(storage):
            # sqlite storages are run sharded, so the storage ids in the run-shard will be
            # different from the storage ids in the index shard.  We therefore cannot
            # compare records directly for sqlite. But we can compare event log entries.
            assert (
                asset_entry.last_materialization_record
                and asset_entry.last_materialization_record.event_log_entry
                == event_log_record.event_log_entry
            )
        else:
            assert asset_entry.last_materialization_record == event_log_record

        # get the planned materialization from the one asset_job run
        materialization_planned_record = storage.get_records_for_run(
            run_id_1,
            of_type=DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
            limit=1,
            ascending=False,
        ).records[0]

        if storage.asset_records_have_last_planned_materialization_storage_id:
            assert (
                asset_entry.last_planned_materialization_storage_id
                == materialization_planned_record.storage_id
            )
        else:
            assert not asset_entry.last_planned_materialization_storage_id

        storage.wipe_asset(my_asset_key)

        # confirm that last_run_id is None when asset is wiped
        assert len(storage.get_asset_records([my_asset_key])) == 0

        result = _execute_job_and_store_events(
            instance,
            storage,
            defs.get_job_def("two_asset_job"),
            run_id=run_id_2,
        )
        records = storage.get_asset_records([my_asset_key])
        assert len(records) == 1
        records = storage.get_asset_records([])  # should select no assets
        assert len(records) == 0

        records = storage.get_asset_records()  # should select all assets
        if self.can_query_all_asset_records():
            assert len(records) == 2
            records = list(records)
            records.sort(key=lambda record: record.asset_entry.asset_key)  # order by asset key
            asset_entry = records[0].asset_entry
            assert asset_entry.asset_key == my_asset_key
            materialize_event = next(
                event for event in result.all_events if event.is_step_materialization
            )
            assert asset_entry.last_materialization
            assert asset_entry.last_materialization.dagster_event == materialize_event
            assert asset_entry.last_run_id == result.run_id
            assert isinstance(asset_entry.asset_details, AssetDetails)
        else:
            assert len(records) == 0

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
        _synthesize_events(lambda: observe_asset(), instance=instance, run_id=run_id_1)
        asset_entry = storage.get_asset_records([asset_key])[0].asset_entry
        assert asset_entry.last_run_id is None

        _synthesize_events(
            lambda: materialize_asset(),
            instance=instance,
            run_id=run_id_2,
        )
        asset_entry = storage.get_asset_records([asset_key])[0].asset_entry
        assert asset_entry.last_run_id == run_id_2

        storage.wipe_asset(asset_key)
        assert len(storage.get_asset_records([asset_key])) == 0

        _synthesize_events(
            lambda: observe_asset(),
            instance=instance,
            run_id=run_id_3,
        )
        asset_entry = storage.get_asset_records([asset_key])[0].asset_entry
        assert asset_entry.last_run_id is None

    def test_asset_record_last_observation(
        self,
        storage: EventLogStorage,
        instance: DagsterInstance,
    ):
        if not storage.asset_records_have_last_observation:
            pytest.skip(
                "storage does not support last_observation events being stored on asset records"
            )

        asset_key = AssetKey("foo")

        @op
        def observe_asset():
            yield AssetObservation("foo")
            yield Output(5)

        run_id = make_new_run_id()
        _synthesize_events(lambda: observe_asset(), instance=instance, run_id=run_id)

        # there is an observation
        fetched_record = storage.fetch_observations(asset_key, limit=1).records[0]
        assert fetched_record

        # the observation is stored on the asset record
        asset_entry = storage.get_asset_records([asset_key])[0].asset_entry
        assert asset_entry.last_observation_record == fetched_record

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
        asset_key = AssetKey("never_materializes_asset")
        never_materializes_job = Definitions(
            assets=[never_materializes_asset],
        ).get_implicit_global_asset_job_def()

        result = _execute_job_and_store_events(
            instance, storage, never_materializes_job, run_id=run_id_1
        )
        records = storage.get_asset_records([asset_key])

        assert len(records) == 1
        asset_record = records[0]
        assert result.run_id == asset_record.asset_entry.last_run_id

        storage.wipe_asset(asset_key)

        # confirm that last_run_id is None when asset is wiped
        assert len(storage.get_asset_records([asset_key])) == 0

        result = _execute_job_and_store_events(
            instance,
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

    def test_get_logs_for_all_runs_by_log_id_by_multi_type(self, storage: EventLogStorage):
        if not storage.supports_event_consumer_queries():
            pytest.skip("storage does not support event consumer queries")

        if not self.supports_multiple_event_type_queries():
            pytest.skip("storage does not support deprecated multi-event-type queries")

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

        run_id_1, run_id_2 = [make_new_run_id() for _ in range(2)]
        for run_id in [run_id_1, run_id_2]:
            events, _ = _synthesize_events(_ops, run_id=run_id)
            for event in events:
                storage.store_event(event)

        events_by_log_id = storage.get_logs_for_all_runs_by_log_id(
            dagster_event_type=DagsterEventType.RUN_SUCCESS,
        )

        assert [event.run_id for event in events_by_log_id.values()] == [run_id_1, run_id_2]
        assert _event_types(events_by_log_id.values()) == [
            DagsterEventType.RUN_SUCCESS,
            DagsterEventType.RUN_SUCCESS,
        ]

        after_cursor_events_by_log_id = storage.get_logs_for_all_runs_by_log_id(
            after_cursor=min(events_by_log_id.keys()),
            dagster_event_type=DagsterEventType.RUN_SUCCESS,
        )

        assert [event.run_id for event in after_cursor_events_by_log_id.values()] == [run_id_2]
        assert _event_types(after_cursor_events_by_log_id.values()) == [
            DagsterEventType.RUN_SUCCESS,
        ]

    def test_get_logs_for_all_runs_by_log_id_cursor_multi_type(self, storage: EventLogStorage):
        if not storage.supports_event_consumer_queries():
            pytest.skip("storage does not support event consumer queries")

        if not self.supports_multiple_event_type_queries():
            pytest.skip("storage does not support deprecated multi-event-type queries")

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

        run_id_1, run_id_2, run_id_3, run_id_4 = [make_new_run_id() for _ in range(4)]
        for run_id in [run_id_1, run_id_2, run_id_3, run_id_4]:
            events, _ = _synthesize_events(_ops, run_id=run_id)
            for event in events:
                storage.store_event(event)

        events_by_log_id = storage.get_logs_for_all_runs_by_log_id(
            dagster_event_type=DagsterEventType.RUN_SUCCESS,
            limit=3,
        )

        assert [event.run_id for event in events_by_log_id.values()] == [
            run_id_1,
            run_id_2,
            run_id_3,
        ]
        assert _event_types(events_by_log_id.values()) == [
            DagsterEventType.RUN_SUCCESS,
            DagsterEventType.RUN_SUCCESS,
            DagsterEventType.RUN_SUCCESS,
        ]

    def test_get_logs_for_all_runs_by_log_id_limit_multi_type(self, storage: EventLogStorage):
        if not storage.supports_event_consumer_queries():
            pytest.skip("storage does not support event consumer queries")

        if not self.supports_multiple_event_type_queries():
            pytest.skip("storage does not support deprecated multi-event-type queries")

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

        storage.store_event(
            EventLogEntry(
                error_info=None,
                level="debug",
                user_message="",
                run_id=make_new_run_id(),
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
                    run_id=make_new_run_id(),
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

        run_id_1 = make_new_run_id()

        _synthesize_events(lambda: my_op(), instance=instance, run_id=run_id_1)

        assert instance.get_materialized_partitions(key) == {
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

        if not self.can_write_cached_status():
            pytest.skip("storage cannot write cached status")

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

            if storage.can_write_asset_status_cache():
                storage.update_asset_cached_status_data(
                    asset_key=asset_key, cache_values=cache_value
                )

                assert _get_cached_status_for_asset(storage, asset_key) == cache_value

                cache_value = AssetStatusCacheValue(
                    latest_storage_id=1,
                    partitions_def_id=None,
                    serialized_materialized_partition_subset=None,
                )

                storage.update_asset_cached_status_data(
                    asset_key=asset_key, cache_values=cache_value
                )
                assert _get_cached_status_for_asset(storage, asset_key) == cache_value

            cache_value = AssetStatusCacheValue(
                latest_storage_id=1,
                partitions_def_id=None,
                serialized_materialized_partition_subset=None,
            )
            storage.update_asset_cached_status_data(asset_key=asset_key, cache_values=cache_value)
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
            assert storage.get_asset_records([asset_key]) == []

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
        if not storage.supports_global_concurrency_limits:
            pytest.skip("storage does not support global op concurrency")

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

        one = make_new_run_id()
        two = make_new_run_id()

        storage.set_concurrency_slots("foo", 1)

        storage.claim_concurrency_slot("foo", one, "a")
        storage.claim_concurrency_slot("foo", two, "b")
        storage.claim_concurrency_slot("foo", one, "c")

        try:
            storage.get_concurrency_run_ids()
        except NotImplementedError:
            pytest.skip("Storage does not implement get_concurrency_run_ids")

        assert storage.get_concurrency_run_ids() == {one, two}
        storage.free_concurrency_slots_for_run(one)
        assert storage.get_concurrency_run_ids() == {two}
        storage.delete_events(run_id=two)
        assert storage.get_concurrency_run_ids() == set()

    def test_threaded_concurrency(self, storage: EventLogStorage):
        if not storage.supports_global_concurrency_limits:
            pytest.skip("storage does not support global op concurrency")

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
        run_id_1, run_id_2, run_id_3 = [make_new_run_id() for _ in range(3)]
        check_key_1 = AssetCheckKey(AssetKey(["my_asset"]), "my_check")
        check_key_2 = AssetCheckKey(AssetKey(["my_asset"]), "my_check_2")

        for asset_key in {AssetKey(["my_asset"]), AssetKey(["my_other_asset"])}:
            storage.store_event(
                EventLogEntry(
                    error_info=None,
                    user_message="",
                    level="debug",
                    run_id=run_id_1,
                    timestamp=time.time(),
                    dagster_event=DagsterEvent(
                        DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED.value,
                        "nonce",
                        event_specific_data=AssetCheckEvaluationPlanned(
                            asset_key=asset_key, check_name="my_check"
                        ),
                    ),
                )
            )

        checks = storage.get_asset_check_execution_history(check_key_1, limit=10)
        assert len(checks) == 1
        assert checks[0].status == AssetCheckExecutionRecordStatus.PLANNED
        assert checks[0].run_id == run_id_1
        assert checks[0].event
        assert checks[0].event.dagster_event_type == DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED

        latest_checks = storage.get_latest_asset_check_execution_by_key([check_key_1, check_key_2])
        assert len(latest_checks) == 1
        assert latest_checks[check_key_1].status == AssetCheckExecutionRecordStatus.PLANNED
        assert latest_checks[check_key_1].run_id == run_id_1

        # update the planned check
        storage.store_event(
            EventLogEntry(
                error_info=None,
                user_message="",
                level="debug",
                run_id=run_id_1,
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
                run_id=run_id_2,
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
        assert checks[0].run_id == run_id_2
        assert checks[1].status == AssetCheckExecutionRecordStatus.SUCCEEDED
        assert checks[1].run_id == run_id_1

        checks = storage.get_asset_check_execution_history(check_key_1, limit=1)
        assert len(checks) == 1
        assert checks[0].run_id == run_id_2

        checks = storage.get_asset_check_execution_history(
            check_key_1, limit=1, cursor=checks[0].id
        )
        assert len(checks) == 1
        assert checks[0].run_id == run_id_1

        latest_checks = storage.get_latest_asset_check_execution_by_key([check_key_1, check_key_2])
        assert len(latest_checks) == 1
        assert latest_checks[check_key_1].status == AssetCheckExecutionRecordStatus.PLANNED
        assert latest_checks[check_key_1].run_id == run_id_2

        storage.store_event(
            EventLogEntry(
                error_info=None,
                user_message="",
                level="debug",
                run_id=run_id_3,
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
        assert latest_checks[check_key_1].run_id == run_id_2
        assert latest_checks[check_key_2].status == AssetCheckExecutionRecordStatus.PLANNED
        assert latest_checks[check_key_2].run_id == run_id_3

    def test_duplicate_asset_check_planned_events(self, storage: EventLogStorage):
        run_id = make_new_run_id()
        for _ in range(2):
            storage.store_event(
                EventLogEntry(
                    error_info=None,
                    user_message="",
                    level="debug",
                    run_id=run_id,
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

        with pytest.raises(
            DagsterInvariantViolationError,
            match="Updated 2 rows for asset check evaluation",
        ):
            storage.store_event(
                EventLogEntry(
                    error_info=None,
                    user_message="",
                    level="debug",
                    run_id=run_id,
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
                                storage_id=42, run_id=run_id, timestamp=3.3
                            ),
                            severity=AssetCheckSeverity.ERROR,
                        ),
                    ),
                )
            )

    def test_asset_check_evaluation_without_planned_event(self, storage: EventLogStorage):
        run_id = make_new_run_id()
        storage.store_event(
            EventLogEntry(
                error_info=None,
                user_message="",
                level="debug",
                run_id=run_id,
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
                            storage_id=42, run_id=run_id, timestamp=3.3
                        ),
                        severity=AssetCheckSeverity.ERROR,
                    ),
                ),
            )
        )

        # since no planned event is logged, we don't create a row in the sumary table
        assert not storage.get_asset_check_execution_history(
            AssetCheckKey(asset_key=AssetKey(["my_asset"]), name="my_check"), limit=10
        )

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

    def test_asset_check_summary_record(
        self,
        storage: EventLogStorage,
        instance: DagsterInstance,
    ) -> None:
        run_id_0, run_id_1 = [make_new_run_id() for _ in range(2)]
        with create_and_delete_test_runs(instance, [run_id_0, run_id_1]):
            check_key_1 = AssetCheckKey(AssetKey(["my_asset"]), "my_check")
            check_key_2 = AssetCheckKey(AssetKey(["my_asset"]), "my_check_2")

            # Initially, records have no last evaluation
            asset_check_summary_records = storage.get_asset_check_summary_records(
                asset_check_keys=[check_key_1, check_key_2]
            )
            assert len(asset_check_summary_records) == 2
            assert all(
                record.last_check_execution_record is None
                for record in asset_check_summary_records.values()
            )
            assert all(
                record.last_run_id is None for record in asset_check_summary_records.values()
            )

            # Store a planned event for both check keys; there should now be a planned record
            # for each.
            storage.store_event(
                EventLogEntry(
                    error_info=None,
                    user_message="",
                    level="debug",
                    run_id=run_id_0,
                    timestamp=time.time(),
                    dagster_event=DagsterEvent(
                        DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED.value,
                        "nonce",
                        event_specific_data=AssetCheckEvaluationPlanned(
                            asset_key=check_key_1.asset_key, check_name=check_key_1.name
                        ),
                    ),
                )
            )

            storage.store_event(
                EventLogEntry(
                    error_info=None,
                    user_message="",
                    level="debug",
                    run_id=run_id_0,
                    timestamp=time.time(),
                    dagster_event=DagsterEvent(
                        DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED.value,
                        "nonce",
                        event_specific_data=AssetCheckEvaluationPlanned(
                            asset_key=check_key_2.asset_key, check_name=check_key_2.name
                        ),
                    ),
                )
            )

            asset_check_summary_records = storage.get_asset_check_summary_records(
                asset_check_keys=[check_key_1, check_key_2]
            )
            assert len(asset_check_summary_records) == 2
            assert all(
                record.last_check_execution_record is not None
                for record in asset_check_summary_records.values()
            )
            assert all(
                record.last_run_id == run_id_0 for record in asset_check_summary_records.values()
            )
            assert all(
                record.last_check_execution_record
                and record.last_check_execution_record.status
                == AssetCheckExecutionRecordStatus.PLANNED
                for record in asset_check_summary_records.values()
            )

            # Store an evaluation for check_key_1
            storage.store_event(
                EventLogEntry(
                    error_info=None,
                    user_message="",
                    level="debug",
                    run_id=run_id_0,
                    timestamp=time.time(),
                    dagster_event=DagsterEvent(
                        DagsterEventType.ASSET_CHECK_EVALUATION.value,
                        "nonce",
                        event_specific_data=AssetCheckEvaluation(
                            asset_key=check_key_1.asset_key,
                            check_name=check_key_1.name,
                            passed=True,
                            metadata={},
                            target_materialization_data=AssetCheckEvaluationTargetMaterializationData(
                                storage_id=42, run_id=run_id_0, timestamp=3.3
                            ),
                            severity=AssetCheckSeverity.ERROR,
                        ),
                    ),
                )
            )

            # Check that the summary record for check_key_1 has been updated,
            # but not 2
            summary_records = storage.get_asset_check_summary_records(
                asset_check_keys=[check_key_1, check_key_2]
            )
            assert len(summary_records) == 2
            check_1_summary_record = summary_records[check_key_1]
            assert check_1_summary_record.last_check_execution_record
            assert (
                check_1_summary_record.last_check_execution_record.status
                == AssetCheckExecutionRecordStatus.SUCCEEDED
            )
            assert check_1_summary_record.last_check_execution_record.run_id == run_id_0

            check_2_summary_record = summary_records[check_key_2]
            assert check_2_summary_record.last_check_execution_record
            assert (
                check_2_summary_record.last_check_execution_record.status
                == AssetCheckExecutionRecordStatus.PLANNED
            )
            assert check_2_summary_record.last_check_execution_record.run_id == run_id_0

            # Store an evaluation for check_key_2
            storage.store_event(
                EventLogEntry(
                    error_info=None,
                    user_message="",
                    level="debug",
                    run_id=run_id_0,
                    timestamp=time.time(),
                    dagster_event=DagsterEvent(
                        DagsterEventType.ASSET_CHECK_EVALUATION.value,
                        "nonce",
                        event_specific_data=AssetCheckEvaluation(
                            asset_key=check_key_2.asset_key,
                            check_name=check_key_2.name,
                            passed=False,
                            metadata={},
                            target_materialization_data=AssetCheckEvaluationTargetMaterializationData(
                                storage_id=42, run_id=run_id_0, timestamp=3.3
                            ),
                            severity=AssetCheckSeverity.ERROR,
                        ),
                    ),
                )
            )

            # Check that the summary record for check_key_2 has been updated
            summary_records = storage.get_asset_check_summary_records(
                asset_check_keys=[check_key_2]
            )

            assert len(summary_records) == 1
            check_2_summary_record = summary_records[check_key_2]
            assert check_2_summary_record.last_check_execution_record
            assert (
                check_2_summary_record.last_check_execution_record.status
                == AssetCheckExecutionRecordStatus.FAILED
            )
            assert check_2_summary_record.last_check_execution_record.run_id == run_id_0

            # Store another planned evaluation for check_key_1
            storage.store_event(
                EventLogEntry(
                    error_info=None,
                    user_message="",
                    level="debug",
                    run_id=run_id_1,
                    timestamp=time.time(),
                    dagster_event=DagsterEvent(
                        DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED.value,
                        "nonce",
                        event_specific_data=AssetCheckEvaluationPlanned(
                            asset_key=check_key_1.asset_key, check_name=check_key_1.name
                        ),
                    ),
                )
            )

            # Check that the summary record for check_key_1 has been updated
            records = storage.get_asset_check_summary_records(asset_check_keys=[check_key_1])
            assert len(records) == 1
            check_1_summary_record = records[check_key_1]
            assert check_1_summary_record.last_check_execution_record
            assert (
                check_1_summary_record.last_check_execution_record.status
                == AssetCheckExecutionRecordStatus.PLANNED
            )
            assert check_1_summary_record.last_check_execution_record.run_id == run_id_1

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

        class BlowUp(Exception): ...

        # now try to delete
        with pytest.raises(BlowUp):
            with storage.index_transaction() as conn:
                conn.execute(SqlEventLogStorageTable.delete())
                # Invalid insert, which should rollback the entire transaction
                raise BlowUp()

        assert len(storage.get_logs_for_run(test_run_id)) == 1

    def test_asset_tags_to_insert(self, test_run_id: str, storage: EventLogStorage):
        key = AssetKey("test_asset")
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
                        materialization=AssetMaterialization(
                            asset_key=key,
                            tags={
                                DATA_VERSION_TAG: "test_data_version",
                                CODE_VERSION_TAG: "test_code_version",
                                _OLD_DATA_VERSION_TAG: "test_old_data_version",
                                f"{INPUT_DATA_VERSION_TAG_PREFIX}/foo": "test_input_data_version",
                                f"{_OLD_INPUT_DATA_VERSION_TAG_PREFIX}/foo": "test_old_input_data_version",
                                f"{INPUT_EVENT_POINTER_TAG_PREFIX}/foo": "1234",
                                DATA_VERSION_IS_USER_PROVIDED_TAG: "test_data_version_is_user_provided",
                                f"{MULTIDIMENSIONAL_PARTITION_PREFIX}foo": "test_multidimensional_partition",
                            },
                        )
                    ),
                ),
            )
        )

        assert storage.get_event_tags_for_asset(key) == [
            {
                DATA_VERSION_TAG: "test_data_version",
                f"{MULTIDIMENSIONAL_PARTITION_PREFIX}foo": "test_multidimensional_partition",
            }
        ]

    def test_previous_observation_data_versions(self, storage, instance):
        asset_key = AssetKey(["one"])
        partitions = ["1", "2", "3"]

        def _observe_partition(partition, data_version):
            yield AssetObservation(
                asset_key=asset_key,
                partition=partition,
                tags={"dagster/data_version": data_version},
            )

        def _observe(data_version):
            for partition in partitions:
                yield from _observe_partition(partition, data_version)

        @op
        def observe_foo():
            yield from _observe("foo")
            yield Output(1)

        @op
        def observe_bar():
            yield from _observe("bar")
            yield Output(1)

        @op
        def observe_foo_bar():
            yield from _observe_partition("1", "bar")
            yield from _observe_partition("2", "bar")
            yield from _observe_partition("3", "foo")
            yield Output(1)

        def _get_last_storage_id(storage):
            return (
                storage.fetch_observations(asset_key, limit=1, ascending=False)
                .records[0]
                .storage_id
            )

        run_id_1, run_id_2, run_id_3 = [make_new_run_id() for i in range(3)]
        with create_and_delete_test_runs(instance, [run_id_1, run_id_2, run_id_3]):
            _synthesize_and_store_events(storage, lambda: observe_foo(), run_id_1)

            after_one = _get_last_storage_id(storage)

            assert storage.get_updated_data_version_partitions(
                asset_key, partitions=partitions, since_storage_id=-1
            ) == {
                "1",
                "2",
                "3",
            }
            assert (
                storage.get_updated_data_version_partitions(
                    asset_key, partitions=partitions, since_storage_id=after_one
                )
                == set()
            )

            # change some of the partitions
            _synthesize_and_store_events(storage, lambda: observe_foo_bar(), run_id_2)
            after_two = _get_last_storage_id(storage)
            assert storage.get_updated_data_version_partitions(
                asset_key, partitions=partitions, since_storage_id=after_one
            ) == {
                "1",
                "2",
            }
            assert (
                storage.get_updated_data_version_partitions(
                    asset_key, partitions=partitions, since_storage_id=after_two
                )
                == set()
            )

            # change the remaining partition
            _synthesize_and_store_events(storage, lambda: observe_bar(), run_id_3)
            after_three = _get_last_storage_id(storage)
            assert storage.get_updated_data_version_partitions(
                asset_key, partitions=partitions, since_storage_id=after_one
            ) == {
                "1",
                "2",
                "3",
            }
            assert storage.get_updated_data_version_partitions(
                asset_key, partitions=partitions, since_storage_id=after_two
            ) == {"3"}
            assert (
                storage.get_updated_data_version_partitions(
                    asset_key, partitions=partitions, since_storage_id=after_three
                )
                == set()
            )

    def test_previous_materialization_data_versions(self, storage, instance):
        asset_key = AssetKey(["one"])
        partitions = ["1", "2", "3"]

        def _materialize_partition(partition, data_version):
            yield AssetMaterialization(
                asset_key=asset_key,
                partition=partition,
                tags={"dagster/data_version": data_version},
            )

        def _materialize(data_version):
            for partition in partitions:
                yield from _materialize_partition(partition, data_version)

        @op
        def materialize_foo():
            yield from _materialize("foo")
            yield Output(1)

        @op
        def materialize_bar():
            yield from _materialize("bar")
            yield Output(1)

        @op
        def materialize_foo_bar():
            yield from _materialize_partition("1", "bar")
            yield from _materialize_partition("2", "bar")
            yield from _materialize_partition("3", "foo")
            yield Output(1)

        def _get_last_storage_id(storage):
            return (
                storage.fetch_materializations(asset_key, limit=1, ascending=False)
                .records[0]
                .storage_id
            )

        run_id_1, run_id_2, run_id_3 = [make_new_run_id() for i in range(3)]
        with create_and_delete_test_runs(instance, [run_id_1, run_id_2, run_id_3]):
            _synthesize_and_store_events(storage, lambda: materialize_foo(), run_id_1)

            after_one = _get_last_storage_id(storage)

            assert storage.get_updated_data_version_partitions(
                asset_key, partitions=partitions, since_storage_id=-1
            ) == {
                "1",
                "2",
                "3",
            }
            assert (
                storage.get_updated_data_version_partitions(
                    asset_key, partitions=partitions, since_storage_id=after_one
                )
                == set()
            )

            # change some of the partitions
            _synthesize_and_store_events(storage, lambda: materialize_foo_bar(), run_id_2)
            after_two = _get_last_storage_id(storage)
            assert storage.get_updated_data_version_partitions(
                asset_key, partitions=partitions, since_storage_id=after_one
            ) == {
                "1",
                "2",
            }
            assert (
                storage.get_updated_data_version_partitions(
                    asset_key, partitions=partitions, since_storage_id=after_two
                )
                == set()
            )

            # change the remaining partition
            _synthesize_and_store_events(storage, lambda: materialize_bar(), run_id_3)
            after_three = _get_last_storage_id(storage)
            assert storage.get_updated_data_version_partitions(
                asset_key, partitions=partitions, since_storage_id=after_one
            ) == {
                "1",
                "2",
                "3",
            }
            assert storage.get_updated_data_version_partitions(
                asset_key, partitions=partitions, since_storage_id=after_two
            ) == {"3"}
            assert (
                storage.get_updated_data_version_partitions(
                    asset_key, partitions=partitions, since_storage_id=after_three
                )
                == set()
            )

    def test_updated_none_data_version(self, storage, instance):
        asset_key = AssetKey(["one"])
        partitions = ["1", "2", "3"]

        def _materialize_partition(partition, data_version):
            tags = {"dagster/data_version": data_version} if data_version else None
            yield AssetMaterialization(asset_key=asset_key, partition=partition, tags=tags)

        def _materialize(data_version):
            for partition in partitions:
                yield from _materialize_partition(partition, data_version)

        @op
        def materialize_foo():
            yield from _materialize("foo")
            yield Output(1)

        @op
        def materialize_bar():
            yield from _materialize("bar")
            yield Output(1)

        @op
        def materialize_none():
            yield from _materialize(None)
            yield Output(1)

        def _get_last_storage_id(storage):
            return (
                storage.fetch_materializations(asset_key, limit=1, ascending=False)
                .records[0]
                .storage_id
            )

        run_id_1, run_id_2, run_id_3 = [make_new_run_id() for i in range(3)]
        with create_and_delete_test_runs(instance, [run_id_1, run_id_2, run_id_3]):
            _synthesize_and_store_events(storage, lambda: materialize_foo(), run_id_1)

            after_one = _get_last_storage_id(storage)

            assert storage.get_updated_data_version_partitions(
                asset_key, partitions=partitions, since_storage_id=-1
            ) == {
                "1",
                "2",
                "3",
            }
            assert (
                storage.get_updated_data_version_partitions(
                    asset_key, partitions=partitions, since_storage_id=after_one
                )
                == set()
            )

            # change data version
            _synthesize_and_store_events(storage, lambda: materialize_bar(), run_id_2)
            after_two = _get_last_storage_id(storage)
            assert storage.get_updated_data_version_partitions(
                asset_key, partitions=partitions, since_storage_id=after_one
            ) == {
                "1",
                "2",
                "3",
            }
            assert (
                storage.get_updated_data_version_partitions(
                    asset_key, partitions=partitions, since_storage_id=after_two
                )
                == set()
            )

            # materialize without data version
            _synthesize_and_store_events(storage, lambda: materialize_none(), run_id_3)
            after_three = _get_last_storage_id(storage)
            assert storage.get_updated_data_version_partitions(
                asset_key, partitions=partitions, since_storage_id=after_one
            ) == {
                "1",
                "2",
                "3",
            }
            assert (
                storage.get_updated_data_version_partitions(
                    asset_key, partitions=partitions, since_storage_id=after_two
                )
                == set()
            )
            assert (
                storage.get_updated_data_version_partitions(
                    asset_key, partitions=partitions, since_storage_id=after_three
                )
                == set()
            )

    def test_get_updated_asset_status_cache_values(
        self, instance: DagsterInstance, storage: EventLogStorage
    ):
        partition_defs_by_key = {
            AssetKey("hourly"): HourlyPartitionsDefinition("2020-01-01-00:00"),
            AssetKey("daily"): DailyPartitionsDefinition("2020-01-01"),
            AssetKey("static"): StaticPartitionsDefinition(["a", "b", "c"]),
        }

        assert storage.get_asset_status_cache_values(
            partition_defs_by_key, LoadingContext.ephemeral(instance)
        ) == [
            None,
            None,
            None,
        ]

        instance.report_runless_asset_event(
            AssetMaterialization(asset_key="hourly", partition="2020-01-01-00:00")
        )
        instance.report_runless_asset_event(
            AssetMaterialization(asset_key="daily", partition="2020-01-01"),
        )
        instance.report_runless_asset_event(AssetMaterialization(asset_key="static", partition="a"))

        partition_defs = list(partition_defs_by_key.values())
        for i, value in enumerate(
            storage.get_asset_status_cache_values(
                partition_defs_by_key, LoadingContext.ephemeral(instance)
            )
        ):
            assert value is not None
            assert len(value.deserialize_materialized_partition_subsets(partition_defs[i])) == 1
