import re
import time
from collections import Counter

import mock
import pytest
from dagster import (
    AssetKey,
    AssetMaterialization,
    EventMetadataEntry,
    InputDefinition,
    ModeDefinition,
    Output,
    OutputDefinition,
    RetryRequested,
    pipeline,
    seven,
    solid,
)
from dagster.core.definitions import ExpectationResult
from dagster.core.definitions.dependency import SolidHandle
from dagster.core.definitions.pipeline_base import InMemoryPipeline
from dagster.core.events import (
    DagsterEvent,
    DagsterEventType,
    EngineEventData,
    StepExpectationResultData,
    StepMaterializationData,
)
from dagster.core.events.log import EventRecord, construct_event_logger
from dagster.core.execution.api import execute_run
from dagster.core.execution.plan.handle import StepHandle
from dagster.core.execution.plan.objects import StepFailureData, StepSuccessData
from dagster.core.execution.stats import StepEventStatus
from dagster.core.storage.event_log import InMemoryEventLogStorage, SqlEventLogStorage
from dagster.core.storage.event_log.migration import REINDEX_DATA_MIGRATIONS, migrate_asset_key_data
from dagster.core.test_utils import instance_for_test
from dagster.core.utils import make_new_run_id
from dagster.loggers import colored_console_logger
from dagster.serdes import deserialize_json_to_dagster_namedtuple
from watchdog.utils import platform

DEFAULT_RUN_ID = "foo"

TEST_TIMEOUT = 5


def create_test_event_log_record(message: str, run_id: str = DEFAULT_RUN_ID):
    return EventRecord(
        None,
        message,
        "debug",
        "",
        run_id,
        time.time(),
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
    solid_handle = SolidHandle(solid_name, None)
    step_handle = StepHandle(solid_handle)
    return EventRecord(
        None,
        "",
        "debug",
        "",
        run_id,
        timestamp,
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


def _mode_def(event_callback):
    return ModeDefinition(
        logger_defs={
            "callback": construct_event_logger(event_callback),
            "console": colored_console_logger,
        }
    )


# This exists to create synthetic events to test the store
def _synthesize_events(solids_fn, run_id=None, check_success=True):
    events = []

    def _append_event(event):
        events.append(event)

    @pipeline(mode_defs=[_mode_def(_append_event)])
    def a_pipe():
        solids_fn()

    with instance_for_test() as instance:
        pipeline_run = instance.create_run_for_pipeline(
            a_pipe, run_id=run_id, run_config={"loggers": {"callback": {}, "console": {}}}
        )

        result = execute_run(InMemoryPipeline(a_pipe), pipeline_run, instance)

        if check_success:
            assert result.success

        return events, result


def _fetch_all_events(configured_storage, run_id=None):
    with configured_storage.run_connection(run_id=run_id) as conn:
        res = conn.execute("SELECT event from event_logs")
        return res.fetchall()


def _event_types(out_events):
    return list(map(lambda e: e.dagster_event.event_type if e.dagster_event else None, out_events))


@solid
def should_succeed(context):
    context.log.info("succeed")
    return "yay"


class TestEventLogStorage:
    """
    You can extend this class to easily run these set of tests on any event log storage. When extending,
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
            yield s

    def test_init_log_storage(self, storage):
        if isinstance(storage, InMemoryEventLogStorage):
            assert not storage.is_persistent
        elif isinstance(storage, SqlEventLogStorage):
            assert storage.is_persistent
        else:
            raise Exception("Invalid event storage type")

    def test_log_storage_run_not_found(self, storage):
        assert storage.get_logs_for_run("bar") == []

    def test_event_log_storage_store_events_and_wipe(self, storage):
        assert len(storage.get_logs_for_run(DEFAULT_RUN_ID)) == 0
        storage.store_event(
            EventRecord(
                None,
                "Message2",
                "debug",
                "",
                DEFAULT_RUN_ID,
                time.time(),
                dagster_event=DagsterEvent(
                    DagsterEventType.ENGINE_EVENT.value,
                    "nonce",
                    event_specific_data=EngineEventData.in_process(999),
                ),
            )
        )
        assert len(storage.get_logs_for_run(DEFAULT_RUN_ID)) == 1
        assert storage.get_stats_for_run(DEFAULT_RUN_ID)
        storage.wipe()
        assert len(storage.get_logs_for_run(DEFAULT_RUN_ID)) == 0

    def test_event_log_storage_store_with_multiple_runs(self, storage):
        runs = ["foo", "bar", "baz"]
        for run_id in runs:
            assert len(storage.get_logs_for_run(run_id)) == 0
            storage.store_event(
                EventRecord(
                    None,
                    "Message2",
                    "debug",
                    "",
                    run_id,
                    time.time(),
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

        storage.wipe()
        for run_id in runs:
            assert len(storage.get_logs_for_run(run_id)) == 0

    @pytest.mark.skipif(
        platform.is_darwin(),
        reason="watchdog's default MacOSX FSEventsObserver sometimes fails to pick up changes",
    )
    def test_event_log_storage_watch(self, storage):
        watched = []
        watcher = lambda x: watched.append(x)  # pylint: disable=unnecessary-lambda

        assert len(storage.get_logs_for_run(DEFAULT_RUN_ID)) == 0

        storage.store_event(create_test_event_log_record(str(1)))
        assert len(storage.get_logs_for_run(DEFAULT_RUN_ID)) == 1
        assert len(watched) == 0

        storage.watch(DEFAULT_RUN_ID, 0, watcher)

        storage.store_event(create_test_event_log_record(str(2)))
        storage.store_event(create_test_event_log_record(str(3)))
        storage.store_event(create_test_event_log_record(str(4)))

        attempts = 10
        while len(watched) < 3 and attempts > 0:
            time.sleep(0.5)
            attempts -= 1
        assert len(watched) == 3

        assert len(storage.get_logs_for_run(DEFAULT_RUN_ID)) == 4

        storage.end_watch(DEFAULT_RUN_ID, watcher)
        time.sleep(0.3)  # this value scientifically selected from a range of attractive values
        storage.store_event(create_test_event_log_record(str(5)))

        assert len(storage.get_logs_for_run(DEFAULT_RUN_ID)) == 5
        assert len(watched) == 3

        storage.delete_events(DEFAULT_RUN_ID)

        assert len(storage.get_logs_for_run(DEFAULT_RUN_ID)) == 0
        assert len(watched) == 3

        assert [int(evt.message) for evt in watched] == [2, 3, 4]

    def test_event_log_storage_pagination(self, storage):
        storage.store_event(create_test_event_log_record(str(0)))
        storage.store_event(create_test_event_log_record(str(1)))
        storage.store_event(create_test_event_log_record(str(2)))

        assert len(storage.get_logs_for_run(DEFAULT_RUN_ID)) == 3
        assert len(storage.get_logs_for_run(DEFAULT_RUN_ID, -1)) == 3
        assert len(storage.get_logs_for_run(DEFAULT_RUN_ID, 0)) == 2
        assert len(storage.get_logs_for_run(DEFAULT_RUN_ID, 1)) == 1
        assert len(storage.get_logs_for_run(DEFAULT_RUN_ID, 2)) == 0

    def test_event_log_delete(self, storage):
        assert len(storage.get_logs_for_run(DEFAULT_RUN_ID)) == 0
        storage.store_event(create_test_event_log_record(str(0)))
        assert len(storage.get_logs_for_run(DEFAULT_RUN_ID)) == 1
        assert storage.get_stats_for_run(DEFAULT_RUN_ID)
        storage.delete_events(DEFAULT_RUN_ID)
        assert len(storage.get_logs_for_run(DEFAULT_RUN_ID)) == 0

    def test_event_log_get_stats_without_start_and_success(self, storage):
        # When an event log doesn't have a PIPELINE_START or PIPELINE_SUCCESS | PIPELINE_FAILURE event,
        # we want to ensure storage.get_stats_for_run(...) doesn't throw an error.
        assert len(storage.get_logs_for_run(DEFAULT_RUN_ID)) == 0
        assert storage.get_stats_for_run(DEFAULT_RUN_ID)

    def test_event_log_get_stats_for_run(self, storage):
        import math

        enqueued_time = time.time()
        launched_time = enqueued_time + 20
        start_time = launched_time + 50
        storage.store_event(
            EventRecord(
                None,
                "message",
                "debug",
                "",
                DEFAULT_RUN_ID,
                enqueued_time,
                dagster_event=DagsterEvent(
                    DagsterEventType.PIPELINE_ENQUEUED.value,
                    "nonce",
                ),
            )
        )
        storage.store_event(
            EventRecord(
                None,
                "message",
                "debug",
                "",
                DEFAULT_RUN_ID,
                launched_time,
                dagster_event=DagsterEvent(
                    DagsterEventType.PIPELINE_STARTING.value,
                    "nonce",
                ),
            )
        )
        storage.store_event(
            EventRecord(
                None,
                "message",
                "debug",
                "",
                DEFAULT_RUN_ID,
                start_time,
                dagster_event=DagsterEvent(
                    DagsterEventType.PIPELINE_START.value,
                    "nonce",
                ),
            )
        )
        assert math.isclose(storage.get_stats_for_run(DEFAULT_RUN_ID).enqueued_time, enqueued_time)
        assert math.isclose(storage.get_stats_for_run(DEFAULT_RUN_ID).launch_time, launched_time)
        assert math.isclose(storage.get_stats_for_run(DEFAULT_RUN_ID).start_time, start_time)

    def test_event_log_step_stats(self, storage):
        # When an event log doesn't have a PIPELINE_START or PIPELINE_SUCCESS | PIPELINE_FAILURE event,
        # we want to ensure storage.get_stats_for_run(...) doesn't throw an error.

        for record in _stats_records(run_id=DEFAULT_RUN_ID):
            storage.store_event(record)

        step_stats = storage.get_step_stats_for_run(DEFAULT_RUN_ID)
        assert len(step_stats) == 4

        a_stats = [stats for stats in step_stats if stats.step_key == "A"][0]
        assert a_stats.step_key == "A"
        assert a_stats.status.value == "SUCCESS"
        assert a_stats.end_time - a_stats.start_time == 100

        b_stats = [stats for stats in step_stats if stats.step_key == "B"][0]
        assert b_stats.step_key == "B"
        assert b_stats.status.value == "FAILURE"
        assert b_stats.end_time - b_stats.start_time == 50

        c_stats = [stats for stats in step_stats if stats.step_key == "C"][0]
        assert c_stats.step_key == "C"
        assert c_stats.status.value == "SKIPPED"
        assert c_stats.end_time - c_stats.start_time == 25

        d_stats = [stats for stats in step_stats if stats.step_key == "D"][0]
        assert d_stats.step_key == "D"
        assert d_stats.status.value == "SUCCESS"
        assert d_stats.end_time - d_stats.start_time == 150
        assert len(d_stats.materializations) == 3
        assert len(d_stats.expectation_results) == 2

    def test_secondary_index(self, storage):
        if not isinstance(storage, SqlEventLogStorage):
            pytest.skip("This test is for SQL-backed Event Log behavior")

        # test that newly initialized DBs will have the secondary indexes built
        for name in REINDEX_DATA_MIGRATIONS.keys():
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

    def test_basic_event_store(self, storage):
        if not isinstance(storage, SqlEventLogStorage):
            pytest.skip("This test is for SQL-backed Event Log behavior")

        @solid
        def return_one(_):
            return 1

        def _solids():
            return_one()

        events, _result = _synthesize_events(_solids, run_id=DEFAULT_RUN_ID)

        for event in events:
            storage.store_event(event)

        rows = _fetch_all_events(storage, run_id=DEFAULT_RUN_ID)

        out_events = list(map(lambda r: deserialize_json_to_dagster_namedtuple(r[0]), rows))

        # messages can come out of order
        event_type_counts = Counter(_event_types(out_events))
        assert event_type_counts
        assert Counter(_event_types(out_events)) == Counter(_event_types(events))

    def test_basic_get_logs_for_run(self, storage):
        @solid
        def return_one(_):
            return 1

        def _solids():
            return_one()

        events, result = _synthesize_events(_solids)

        for event in events:
            storage.store_event(event)

        out_events = storage.get_logs_for_run(result.run_id)

        assert _event_types(out_events) == _event_types(events)

    def test_wipe_sql_backed_event_log(self, storage):
        @solid
        def return_one(_):
            return 1

        def _solids():
            return_one()

        events, result = _synthesize_events(_solids)

        for event in events:
            storage.store_event(event)

        out_events = storage.get_logs_for_run(result.run_id)

        assert _event_types(out_events) == _event_types(events)

        storage.wipe()

        assert storage.get_logs_for_run(result.run_id) == []

    def test_delete_sql_backed_event_log(self, storage):
        @solid
        def return_one(_):
            return 1

        def _solids():
            return_one()

        events, result = _synthesize_events(_solids)

        for event in events:
            storage.store_event(event)

        out_events = storage.get_logs_for_run(result.run_id)

        assert _event_types(out_events) == _event_types(events)

        storage.delete_events(result.run_id)

        assert storage.get_logs_for_run(result.run_id) == []

    @pytest.mark.skip("https://github.com/dagster-io/dagster/issues/3621")
    def test_basic_get_logs_for_run_cursor(self, storage):
        @solid
        def return_one(_):
            return 1

        def _solids():
            return_one()

        events, result = _synthesize_events(_solids)

        for event in events:
            storage.store_event(event)

        assert _event_types(storage.get_logs_for_run(result.run_id, cursor=0)) == _event_types(
            events
        )

        assert _event_types(storage.get_logs_for_run(result.run_id, cursor=1)) == _event_types(
            events
        )

    def test_basic_get_logs_for_run_multiple_runs(self, storage):
        @solid
        def return_one(_):
            return 1

        def _solids():
            return_one()

        events_one, result_one = _synthesize_events(_solids)
        for event in events_one:
            storage.store_event(event)

        events_two, result_two = _synthesize_events(_solids)
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

    @pytest.mark.skip("https://github.com/dagster-io/dagster/issues/3621")
    def test_basic_get_logs_for_run_multiple_runs_cursors(self, storage):
        @solid
        def return_one(_):
            return 1

        def _solids():
            return_one()

        events_one, result_one = _synthesize_events(_solids)
        for event in events_one:
            storage.store_event(event)

        events_two, result_two = _synthesize_events(_solids)
        for event in events_two:
            storage.store_event(event)

        out_events_one = storage.get_logs_for_run(result_one.run_id, cursor=1)
        assert len(out_events_one) == len(events_one)

        assert set(_event_types(out_events_one)) == set(_event_types(events_one))

        assert set(map(lambda e: e.run_id, out_events_one)) == {result_one.run_id}

        out_events_two = storage.get_logs_for_run(result_two.run_id, cursor=2)
        assert len(out_events_two) == len(events_two)
        assert set(_event_types(out_events_two)) == set(_event_types(events_one))

        assert set(map(lambda e: e.run_id, out_events_two)) == {result_two.run_id}

    def test_event_watcher_single_run_event(self, storage):
        if not hasattr(storage, "event_watcher"):
            pytest.skip("This test requires an event_watcher attribute")

        @solid
        def return_one(_):
            return 1

        def _solids():
            return_one()

        event_list = []

        run_id = make_new_run_id()

        storage.event_watcher.watch_run(run_id, -1, event_list.append)

        events, _ = _synthesize_events(_solids, run_id=run_id)
        for event in events:
            storage.store_event(event)

        start = time.time()
        while len(event_list) < len(events) and time.time() - start < TEST_TIMEOUT:
            pass

        assert len(event_list) == len(events)
        assert all([isinstance(event, EventRecord) for event in event_list])

    def test_event_watcher_filter_run_event(self, storage):
        if not hasattr(storage, "event_watcher"):
            pytest.skip("This test requires an event_watcher attribute")

        @solid
        def return_one(_):
            return 1

        def _solids():
            return_one()

        run_id_one = make_new_run_id()
        run_id_two = make_new_run_id()

        # only watch one of the runs
        event_list = []
        storage.event_watcher.watch_run(run_id_two, 0, event_list.append)

        events_one, _result_one = _synthesize_events(_solids, run_id=run_id_one)
        for event in events_one:
            storage.store_event(event)

        events_two, _result_two = _synthesize_events(_solids, run_id=run_id_two)
        for event in events_two:
            storage.store_event(event)

        start = time.time()
        while len(event_list) < len(events_two) and time.time() - start < TEST_TIMEOUT:
            pass

        assert len(event_list) == len(events_two)
        assert all([isinstance(event, EventRecord) for event in event_list])

    def test_event_watcher_filter_two_runs_event(self, storage):
        if not hasattr(storage, "event_watcher"):
            pytest.skip("This test requires an event_watcher attribute")

        @solid
        def return_one(_):
            return 1

        def _solids():
            return_one()

        event_list_one = []
        event_list_two = []

        run_id_one = make_new_run_id()
        run_id_two = make_new_run_id()

        storage.event_watcher.watch_run(run_id_one, -1, event_list_one.append)
        storage.event_watcher.watch_run(run_id_two, -1, event_list_two.append)

        events_one, _result_one = _synthesize_events(_solids, run_id=run_id_one)
        for event in events_one:
            storage.store_event(event)

        events_two, _result_two = _synthesize_events(_solids, run_id=run_id_two)
        for event in events_two:
            storage.store_event(event)

        start = time.time()
        while (
            len(event_list_one) < len(events_one) or len(event_list_two) < len(events_two)
        ) and time.time() - start < TEST_TIMEOUT:
            pass

        assert len(event_list_one) == len(events_one)
        assert len(event_list_two) == len(events_two)
        assert all([isinstance(event, EventRecord) for event in event_list_one])
        assert all([isinstance(event, EventRecord) for event in event_list_two])

    def test_correct_timezone(self, storage):
        curr_time = time.time()

        event = EventRecord(
            None,
            "Message2",
            "debug",
            "",
            "foo",
            curr_time,
            dagster_event=DagsterEvent(
                DagsterEventType.PIPELINE_START.value,
                "nonce",
                event_specific_data=EngineEventData.in_process(999),
            ),
        )

        storage.store_event(event)

        logs = storage.get_logs_for_run("foo")

        assert len(logs) == 1

        log = logs[0]

        stats = storage.get_stats_for_run("foo")

        assert int(log.timestamp) == int(stats.start_time)
        assert int(log.timestamp) == int(curr_time)

    def test_asset_materialization(self, storage):
        asset_key = AssetKey(["path", "to", "asset_one"])

        @solid
        def materialize_one(_):
            yield AssetMaterialization(
                asset_key=asset_key,
                metadata_entries=[
                    EventMetadataEntry.text("hello", "text"),
                    EventMetadataEntry.json({"hello": "world"}, "json"),
                    EventMetadataEntry.float(1.0, "one_float"),
                    EventMetadataEntry.int(1, "one_int"),
                ],
            )
            yield Output(1)

        def _solids():
            materialize_one()

        events_one, _ = _synthesize_events(_solids)
        for event in events_one:
            storage.store_event(event)

        assert asset_key in set(storage.all_asset_keys())
        events = storage.get_asset_events(asset_key)
        assert len(events) == 1
        event = events[0]
        assert isinstance(event, EventRecord)
        assert event.dagster_event.event_type_value == DagsterEventType.ASSET_MATERIALIZATION.value

    def test_asset_events_error_parsing(self, storage):
        if not isinstance(storage, SqlEventLogStorage):
            pytest.skip("This test is for SQL-backed Event Log behavior")
        _logs = []

        def mock_log(msg):
            _logs.append(msg)

        asset_key = AssetKey("asset_one")

        @solid
        def materialize_one(_):
            yield AssetMaterialization(asset_key=asset_key)
            yield Output(1)

        def _solids():
            materialize_one()

        events_one, _ = _synthesize_events(_solids)
        for event in events_one:
            storage.store_event(event)

        with mock.patch(
            "dagster.core.storage.event_log.sql_event_log.logging.warning",
            side_effect=mock_log,
        ):
            with mock.patch(
                "dagster.core.storage.event_log.sql_event_log.deserialize_json_to_dagster_namedtuple",
                return_value="not_an_event_record",
            ):

                assert asset_key in set(storage.all_asset_keys())
                events = storage.get_asset_events(asset_key)
                assert len(events) == 0
                assert len(_logs) == 1
                assert re.match("Could not resolve asset event record as EventRecord", _logs[0])

            _logs = []  # reset logs

            with mock.patch(
                "dagster.core.storage.event_log.sql_event_log.deserialize_json_to_dagster_namedtuple",
                side_effect=seven.JSONDecodeError("error", "", 0),
            ):
                assert asset_key in set(storage.all_asset_keys())
                events = storage.get_asset_events(asset_key)
                assert len(events) == 0
                assert len(_logs) == 1
                assert re.match("Could not parse asset event record id", _logs[0])

    def test_secondary_index_asset_keys(self, storage):
        asset_key_one = AssetKey(["one"])
        asset_key_two = AssetKey(["two"])

        @solid
        def materialize_one(_):
            yield AssetMaterialization(asset_key=asset_key_one)
            yield Output(1)

        @solid
        def materialize_two(_):
            yield AssetMaterialization(asset_key=asset_key_two)
            yield Output(1)

        def _one():
            materialize_one()

        def _two():
            materialize_two()

        events_one, _ = _synthesize_events(_one)
        for event in events_one:
            storage.store_event(event)

        asset_keys = storage.all_asset_keys()
        assert len(asset_keys) == 1
        assert asset_key_one in set(asset_keys)
        migrate_asset_key_data(storage)
        asset_keys = storage.all_asset_keys()
        assert len(asset_keys) == 1
        assert asset_key_one in set(asset_keys)
        events_two, _ = _synthesize_events(_two)
        for event in events_two:
            storage.store_event(event)
        asset_keys = storage.all_asset_keys()
        assert len(asset_keys) == 2
        assert asset_key_one in set(asset_keys)
        assert asset_key_two in set(asset_keys)

    def test_run_step_stats(self, storage):
        @solid(input_defs=[InputDefinition("_input", str)], output_defs=[OutputDefinition(str)])
        def should_fail(context, _input):
            context.log.info("fail")
            raise Exception("booo")

        def _one():
            should_fail(should_succeed())

        events, result = _synthesize_events(_one, check_success=False)
        for event in events:
            storage.store_event(event)

        step_stats = sorted(storage.get_step_stats_for_run(result.run_id), key=lambda x: x.end_time)
        assert len(step_stats) == 2
        assert step_stats[0].step_key == "should_succeed"
        assert step_stats[0].status == StepEventStatus.SUCCESS
        assert step_stats[0].end_time > step_stats[0].start_time
        assert step_stats[0].attempts == 1
        assert step_stats[1].step_key == "should_fail"
        assert step_stats[1].status == StepEventStatus.FAILURE
        assert step_stats[1].end_time > step_stats[0].start_time
        assert step_stats[1].attempts == 1

    def test_run_step_stats_with_retries(self, storage):
        @solid(input_defs=[InputDefinition("_input", str)], output_defs=[OutputDefinition(str)])
        def should_retry(context, _input):
            raise RetryRequested(max_retries=3)

        def _one():
            should_retry(should_succeed())

        events, result = _synthesize_events(_one, check_success=False)
        for event in events:
            storage.store_event(event)

        step_stats = storage.get_step_stats_for_run(result.run_id, step_keys=["should_retry"])
        assert len(step_stats) == 1
        assert step_stats[0].step_key == "should_retry"
        assert step_stats[0].status == StepEventStatus.FAILURE
        assert step_stats[0].end_time > step_stats[0].start_time
        assert step_stats[0].attempts == 4
