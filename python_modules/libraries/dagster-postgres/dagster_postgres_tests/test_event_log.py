import re
import time
from collections import Counter

import mock
import pytest
import yaml
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
from dagster.core.definitions.pipeline_base import InMemoryPipeline
from dagster.core.events import DagsterEvent, DagsterEventType, EngineEventData
from dagster.core.events.log import EventRecord, construct_event_logger
from dagster.core.execution.api import execute_run
from dagster.core.execution.stats import StepEventStatus
from dagster.core.storage.event_log.migration import migrate_asset_key_data
from dagster.core.test_utils import instance_for_test
from dagster.core.utils import make_new_run_id
from dagster.loggers import colored_console_logger
from dagster.serdes import deserialize_json_to_dagster_namedtuple
from dagster_postgres.event_log import PostgresEventLogStorage
from dagster_postgres.utils import get_conn

TEST_TIMEOUT = 5


def mode_def(event_callback):
    return ModeDefinition(
        logger_defs={
            "callback": construct_event_logger(event_callback),
            "console": colored_console_logger,
        }
    )


# This just exists to create synthetic events to test the store
def synthesize_events(solids_fn, run_id=None, check_success=True):
    events = []

    def _append_event(event):
        events.append(event)

    @pipeline(mode_defs=[mode_def(_append_event)])
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


def fetch_all_events(conn_string):
    conn = get_conn(conn_string)
    with conn.cursor() as curs:
        curs.execute("SELECT event from event_logs")
        return curs.fetchall()


def test_basic_event_store(conn_string):
    @solid
    def return_one(_):
        return 1

    def _solids():
        return_one()

    events, _result = synthesize_events(_solids)

    event_log_storage = PostgresEventLogStorage.create_clean_storage(conn_string)

    for event in events:
        event_log_storage.store_event(event)

    rows = fetch_all_events(conn_string)

    out_events = list(map(lambda r: deserialize_json_to_dagster_namedtuple(r[0]), rows))

    # messages can come out of order
    event_type_counts = Counter(event_types(out_events))
    assert event_type_counts
    assert Counter(event_types(out_events)) == Counter(event_types(events))


def event_types(out_events):
    return list(map(lambda e: e.dagster_event.event_type if e.dagster_event else None, out_events))


def sorted_event_types(out_events):
    return event_types(sorted(out_events, key=lambda x: x.timestamp))


def test_basic_get_logs_for_run(conn_string):
    @solid
    def return_one(_):
        return 1

    def _solids():
        return_one()

    events, result = synthesize_events(_solids)

    event_log_storage = PostgresEventLogStorage.create_clean_storage(conn_string)

    for event in events:
        event_log_storage.store_event(event)

    out_events = event_log_storage.get_logs_for_run(result.run_id)

    assert event_types(out_events) == event_types(events)


def test_wipe_postgres_event_log(conn_string):
    @solid
    def return_one(_):
        return 1

    def _solids():
        return_one()

    events, result = synthesize_events(_solids)

    event_log_storage = PostgresEventLogStorage.create_clean_storage(conn_string)

    for event in events:
        event_log_storage.store_event(event)

    out_events = event_log_storage.get_logs_for_run(result.run_id)

    assert event_types(out_events) == event_types(events)

    event_log_storage.wipe()

    assert event_log_storage.get_logs_for_run(result.run_id) == []


def test_delete_postgres_event_log(conn_string):
    @solid
    def return_one(_):
        return 1

    def _solids():
        return_one()

    events, result = synthesize_events(_solids)

    event_log_storage = PostgresEventLogStorage.create_clean_storage(conn_string)

    for event in events:
        event_log_storage.store_event(event)

    out_events = event_log_storage.get_logs_for_run(result.run_id)

    assert event_types(out_events) == event_types(events)

    event_log_storage.delete_events(result.run_id)

    assert event_log_storage.get_logs_for_run(result.run_id) == []


@pytest.mark.skip("https://github.com/dagster-io/dagster/issues/3621")
def test_basic_get_logs_for_run_cursor(conn_string):
    event_log_storage = PostgresEventLogStorage.create_clean_storage(conn_string)

    @solid
    def return_one(_):
        return 1

    def _solids():
        return_one()

    events, result = synthesize_events(_solids)

    for event in events:
        event_log_storage.store_event(event)

    assert event_types(event_log_storage.get_logs_for_run(result.run_id, cursor=0)) == event_types(
        events
    )

    assert event_types(event_log_storage.get_logs_for_run(result.run_id, cursor=1)) == event_types(
        events
    )


def test_basic_get_logs_for_run_multiple_runs(conn_string):
    event_log_storage = PostgresEventLogStorage.create_clean_storage(conn_string)

    @solid
    def return_one(_):
        return 1

    def _solids():
        return_one()

    events_one, result_one = synthesize_events(_solids)
    for event in events_one:
        event_log_storage.store_event(event)

    events_two, result_two = synthesize_events(_solids)
    for event in events_two:
        event_log_storage.store_event(event)

    out_events_one = event_log_storage.get_logs_for_run(result_one.run_id)
    assert len(out_events_one) == len(events_one)

    assert set(event_types(out_events_one)) == set(event_types(events_one))

    assert set(map(lambda e: e.run_id, out_events_one)) == {result_one.run_id}

    stats_one = event_log_storage.get_stats_for_run(result_one.run_id)
    assert stats_one.steps_succeeded == 1

    out_events_two = event_log_storage.get_logs_for_run(result_two.run_id)
    assert len(out_events_two) == len(events_two)

    assert set(event_types(out_events_two)) == set(event_types(events_two))

    assert set(map(lambda e: e.run_id, out_events_two)) == {result_two.run_id}

    stats_two = event_log_storage.get_stats_for_run(result_two.run_id)
    assert stats_two.steps_succeeded == 1


@pytest.mark.skip("https://github.com/dagster-io/dagster/issues/3621")
def test_basic_get_logs_for_run_multiple_runs_cursors(conn_string):
    event_log_storage = PostgresEventLogStorage.create_clean_storage(conn_string)

    @solid
    def return_one(_):
        return 1

    def _solids():
        return_one()

    events_one, result_one = synthesize_events(_solids)
    for event in events_one:
        event_log_storage.store_event(event)

    events_two, result_two = synthesize_events(_solids)
    for event in events_two:
        event_log_storage.store_event(event)

    out_events_one = event_log_storage.get_logs_for_run(result_one.run_id, cursor=1)
    assert len(out_events_one) == len(events_one)

    assert set(event_types(out_events_one)) == set(event_types(events_one))

    assert set(map(lambda e: e.run_id, out_events_one)) == {result_one.run_id}

    out_events_two = event_log_storage.get_logs_for_run(result_two.run_id, cursor=2)
    assert len(out_events_two) == len(events_two)
    assert set(event_types(out_events_two)) == set(event_types(events_one))

    assert set(map(lambda e: e.run_id, out_events_two)) == {result_two.run_id}


def test_listen_notify_single_run_event(conn_string):
    event_log_storage = PostgresEventLogStorage.create_clean_storage(conn_string)

    @solid
    def return_one(_):
        return 1

    def _solids():
        return_one()

    event_list = []

    run_id = make_new_run_id()

    event_log_storage.event_watcher.watch_run(run_id, 0, event_list.append)

    try:
        events, _ = synthesize_events(_solids, run_id=run_id)
        for event in events:
            event_log_storage.store_event(event)

        start = time.time()
        while len(event_list) < len(events) and time.time() - start < TEST_TIMEOUT:
            pass

        assert len(event_list) == len(events)
        # uncomment when https://github.com/dagster-io/dagster/issues/3368 is resolved with structured event
        # assert all([isinstance(event, EventRecord) for event in event_list])
    finally:
        del event_log_storage


def test_listen_notify_filter_two_runs_event(conn_string):
    event_log_storage = PostgresEventLogStorage.create_clean_storage(conn_string)

    @solid
    def return_one(_):
        return 1

    def _solids():
        return_one()

    event_list_one = []
    event_list_two = []

    run_id_one = make_new_run_id()
    run_id_two = make_new_run_id()

    event_log_storage.event_watcher.watch_run(run_id_one, 0, event_list_one.append)
    event_log_storage.event_watcher.watch_run(run_id_two, 0, event_list_two.append)

    try:
        events_one, _result_one = synthesize_events(_solids, run_id=run_id_one)
        for event in events_one:
            event_log_storage.store_event(event)

        events_two, _result_two = synthesize_events(_solids, run_id=run_id_two)
        for event in events_two:
            event_log_storage.store_event(event)

        start = time.time()
        while (
            len(event_list_one) < len(events_one) or len(event_list_two) < len(events_two)
        ) and time.time() - start < TEST_TIMEOUT:
            pass

        assert len(event_list_one) == len(events_one)
        assert len(event_list_two) == len(events_two)
        # uncomment when https://github.com/dagster-io/dagster/issues/3368 is resolved with structured event
        # assert all([isinstance(event, EventRecord) for event in event_list_one])
        # assert all([isinstance(event, EventRecord) for event in event_list_two])

    finally:
        del event_log_storage


def test_listen_notify_filter_run_event(conn_string):
    event_log_storage = PostgresEventLogStorage.create_clean_storage(conn_string)

    @solid
    def return_one(_):
        return 1

    def _solids():
        return_one()

    run_id_one = make_new_run_id()
    run_id_two = make_new_run_id()

    # only watch one of the runs
    event_list = []
    event_log_storage.event_watcher.watch_run(run_id_two, 0, event_list.append)

    try:
        events_one, _result_one = synthesize_events(_solids, run_id=run_id_one)
        for event in events_one:
            event_log_storage.store_event(event)

        events_two, _result_two = synthesize_events(_solids, run_id=run_id_two)
        for event in events_two:
            event_log_storage.store_event(event)

        start = time.time()
        while len(event_list) < len(events_two) and time.time() - start < TEST_TIMEOUT:
            pass

        assert len(event_list) == len(events_two)
        # uncomment when https://github.com/dagster-io/dagster/issues/3368 is resolved with structured event
        # assert all([isinstance(event, EventRecord) for event in event_list])

    finally:
        del event_log_storage


def test_load_from_config(hostname):
    url_cfg = """
      event_log_storage:
        module: dagster_postgres.event_log
        class: PostgresEventLogStorage
        config:
            postgres_url: postgresql://test:test@{hostname}:5432/test
    """.format(
        hostname=hostname
    )

    explicit_cfg = """
      event_log_storage:
        module: dagster_postgres.event_log
        class: PostgresEventLogStorage
        config:
            postgres_db:
              username: test
              password: test
              hostname: {hostname}
              db_name: test
    """.format(
        hostname=hostname
    )

    # pylint: disable=protected-access
    with instance_for_test(overrides=yaml.safe_load(url_cfg)) as from_url_instance:
        from_url = from_url_instance._event_storage

        with instance_for_test(overrides=yaml.safe_load(explicit_cfg)) as explicit_instance:
            from_explicit = explicit_instance._event_storage

            assert from_url.postgres_url == from_explicit.postgres_url


def test_correct_timezone(conn_string):
    event_log_storage = PostgresEventLogStorage.create_clean_storage(conn_string)

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

    event_log_storage.store_event(event)

    logs = event_log_storage.get_logs_for_run("foo")

    assert len(logs) == 1

    log = logs[0]

    stats = event_log_storage.get_stats_for_run("foo")

    assert int(log.timestamp) == int(stats.start_time)
    assert int(log.timestamp) == int(curr_time)


def test_asset_materialization(conn_string):
    event_log_storage = PostgresEventLogStorage.create_clean_storage(conn_string)

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

    events_one, _ = synthesize_events(_solids)
    for event in events_one:
        event_log_storage.store_event(event)

    assert asset_key in set(event_log_storage.get_all_asset_keys())
    events = event_log_storage.get_asset_events(asset_key)
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, EventRecord)
    assert event.dagster_event.event_type_value == DagsterEventType.STEP_MATERIALIZATION.value


def test_asset_events_error_parsing(conn_string):
    event_log_storage = PostgresEventLogStorage.create_clean_storage(conn_string)
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

    events_one, _ = synthesize_events(_solids)
    for event in events_one:
        event_log_storage.store_event(event)

    with mock.patch(
        "dagster.core.storage.event_log.sql_event_log.logging.warning",
        side_effect=mock_log,
    ):
        with mock.patch(
            "dagster.core.storage.event_log.sql_event_log.deserialize_json_to_dagster_namedtuple",
            return_value="not_an_event_record",
        ):

            assert asset_key in set(event_log_storage.get_all_asset_keys())
            events = event_log_storage.get_asset_events(asset_key)
            assert len(events) == 0
            assert len(_logs) == 1
            assert re.match("Could not resolve asset event record as EventRecord", _logs[0])

        _logs = []  # reset logs

        with mock.patch(
            "dagster.core.storage.event_log.sql_event_log.deserialize_json_to_dagster_namedtuple",
            side_effect=seven.JSONDecodeError("error", "", 0),
        ):
            assert asset_key in set(event_log_storage.get_all_asset_keys())
            events = event_log_storage.get_asset_events(asset_key)
            assert len(events) == 0
            assert len(_logs) == 1
            assert re.match("Could not parse asset event record id", _logs[0])


def test_secondary_index_asset_keys(conn_string):
    event_log_storage = PostgresEventLogStorage.create_clean_storage(conn_string)

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

    events_one, _ = synthesize_events(_one)
    for event in events_one:
        event_log_storage.store_event(event)

    asset_keys = event_log_storage.get_all_asset_keys()
    assert len(asset_keys) == 1
    assert asset_key_one in set(asset_keys)
    migrate_asset_key_data(event_log_storage)
    asset_keys = event_log_storage.get_all_asset_keys()
    assert len(asset_keys) == 1
    assert asset_key_one in set(asset_keys)
    events_two, _ = synthesize_events(_two)
    for event in events_two:
        event_log_storage.store_event(event)
    asset_keys = event_log_storage.get_all_asset_keys()
    assert len(asset_keys) == 2
    assert asset_key_one in set(asset_keys)
    assert asset_key_two in set(asset_keys)


@solid
def should_succeed(context):
    context.log.info("succeed")
    return "yay"


def test_run_step_stats(conn_string):
    event_log_storage = PostgresEventLogStorage.create_clean_storage(conn_string)

    @solid(input_defs=[InputDefinition("_input", str)], output_defs=[OutputDefinition(str)])
    def should_fail(context, _input):
        context.log.info("fail")
        raise Exception("booo")

    def _one():
        should_fail(should_succeed())

    events, result = synthesize_events(_one, check_success=False)
    for event in events:
        event_log_storage.store_event(event)

    step_stats = sorted(
        event_log_storage.get_step_stats_for_run(result.run_id), key=lambda x: x.end_time
    )
    assert len(step_stats) == 2
    assert step_stats[0].step_key == "should_succeed"
    assert step_stats[0].status == StepEventStatus.SUCCESS
    assert step_stats[0].end_time > step_stats[0].start_time
    assert step_stats[0].attempts == 1
    assert step_stats[1].step_key == "should_fail"
    assert step_stats[1].status == StepEventStatus.FAILURE
    assert step_stats[1].end_time > step_stats[0].start_time
    assert step_stats[1].attempts == 1


def test_run_step_stats_with_retries(conn_string):
    event_log_storage = PostgresEventLogStorage.create_clean_storage(conn_string)

    @solid(input_defs=[InputDefinition("_input", str)], output_defs=[OutputDefinition(str)])
    def should_retry(context, _input):
        raise RetryRequested(max_retries=3)

    def _one():
        should_retry(should_succeed())

    events, result = synthesize_events(_one, check_success=False)
    for event in events:
        event_log_storage.store_event(event)

    step_stats = event_log_storage.get_step_stats_for_run(result.run_id, step_keys=["should_retry"])
    assert len(step_stats) == 1
    assert step_stats[0].step_key == "should_retry"
    assert step_stats[0].status == StepEventStatus.FAILURE
    assert step_stats[0].end_time > step_stats[0].start_time
    assert step_stats[0].attempts == 4
