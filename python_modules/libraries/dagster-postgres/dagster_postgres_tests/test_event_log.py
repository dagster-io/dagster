import uuid

from dagster_postgres.event_log import (
    EventWatcherEvent,
    EventWatcherStart,
    PostgresEventLogStorage,
    create_event_watcher,
)
from dagster_postgres.test import get_test_conn_string
from dagster_postgres.utils import get_conn

from dagster import ModeDefinition, RunConfig, execute_pipeline, pipeline, solid
from dagster.core.events import DagsterEventType
from dagster.core.events.log import construct_event_logger
from dagster.core.serdes import deserialize_json_to_dagster_namedtuple
from dagster.loggers import colored_console_logger


def mode_def(event_callback):
    return ModeDefinition(
        logger_defs={
            'callback': construct_event_logger(event_callback),
            'console': colored_console_logger,
        }
    )


# This just exists to gather synthetic events to test the store
def gather_events(solids_fn, run_config=None):
    events = []

    def _append_event(event):
        events.append(event)

    @pipeline(mode_defs=[mode_def(_append_event)])
    def a_pipe():
        solids_fn()

    result = execute_pipeline(
        a_pipe, {'loggers': {'callback': {}, 'console': {}}}, run_config=run_config
    )

    assert result.success

    return events, result


def fetch_all_events(conn_string):
    conn = get_conn(conn_string)
    with conn.cursor() as curs:
        curs.execute('SELECT event_body from event_log')
        return curs.fetchall()


def test_basic_event_store():
    @solid
    def return_one(_):
        return 1

    def _solids():
        return_one()  # pylint: disable=no-value-for-parameter

    events, _result = gather_events(_solids)

    event_log_storage = PostgresEventLogStorage.create_nuked_storage(get_test_conn_string())

    for event in events:
        event_log_storage.store_event(event)

    rows = fetch_all_events(get_test_conn_string())

    out_events = list(map(lambda r: deserialize_json_to_dagster_namedtuple(r[0]), rows))

    assert list(map(lambda e: e.dagster_event.event_type, out_events)) == [
        DagsterEventType.PIPELINE_START,
        DagsterEventType.ENGINE_EVENT,
        DagsterEventType.STEP_START,
        DagsterEventType.STEP_OUTPUT,
        DagsterEventType.STEP_SUCCESS,
        DagsterEventType.ENGINE_EVENT,
        DagsterEventType.PIPELINE_SUCCESS,
    ]


def event_types(out_events):
    return list(map(lambda e: e.dagster_event.event_type, out_events))


def test_basic_get_logs_for_run():
    @solid
    def return_one(_):
        return 1

    def _solids():
        return_one()  # pylint: disable=no-value-for-parameter

    events, result = gather_events(_solids)

    event_log_storage = PostgresEventLogStorage.create_nuked_storage(get_test_conn_string())

    for event in events:
        event_log_storage.store_event(event)

    out_events = event_log_storage.get_logs_for_run(result.run_id)

    assert event_types(out_events) == [
        DagsterEventType.PIPELINE_START,
        DagsterEventType.ENGINE_EVENT,
        DagsterEventType.STEP_START,
        DagsterEventType.STEP_OUTPUT,
        DagsterEventType.STEP_SUCCESS,
        DagsterEventType.ENGINE_EVENT,
        DagsterEventType.PIPELINE_SUCCESS,
    ]


def test_wipe_postgres_event_log():
    @solid
    def return_one(_):
        return 1

    def _solids():
        return_one()  # pylint: disable=no-value-for-parameter

    events, result = gather_events(_solids)

    event_log_storage = PostgresEventLogStorage.create_nuked_storage(get_test_conn_string())

    for event in events:
        event_log_storage.store_event(event)

    out_events = event_log_storage.get_logs_for_run(result.run_id)

    assert event_types(out_events) == [
        DagsterEventType.PIPELINE_START,
        DagsterEventType.ENGINE_EVENT,
        DagsterEventType.STEP_START,
        DagsterEventType.STEP_OUTPUT,
        DagsterEventType.STEP_SUCCESS,
        DagsterEventType.ENGINE_EVENT,
        DagsterEventType.PIPELINE_SUCCESS,
    ]

    event_log_storage.wipe()

    assert event_log_storage.get_logs_for_run(result.run_id) == []


def test_basic_get_logs_for_run_cursor():
    event_log_storage = PostgresEventLogStorage.create_nuked_storage(get_test_conn_string())

    @solid
    def return_one(_):
        return 1

    def _solids():
        return_one()  # pylint: disable=no-value-for-parameter

    events, result = gather_events(_solids)

    for event in events:
        event_log_storage.store_event(event)

    assert event_types(event_log_storage.get_logs_for_run(result.run_id, cursor=0)) == [
        # DagsterEventType.PIPELINE_START,
        DagsterEventType.ENGINE_EVENT,
        DagsterEventType.STEP_START,
        DagsterEventType.STEP_OUTPUT,
        DagsterEventType.STEP_SUCCESS,
        DagsterEventType.ENGINE_EVENT,
        DagsterEventType.PIPELINE_SUCCESS,
    ]

    assert event_types(event_log_storage.get_logs_for_run(result.run_id, cursor=1)) == [
        # DagsterEventType.PIPELINE_START,
        # DagsterEventType.ENGINE_EVENT,
        DagsterEventType.STEP_START,
        DagsterEventType.STEP_OUTPUT,
        DagsterEventType.STEP_SUCCESS,
        DagsterEventType.ENGINE_EVENT,
        DagsterEventType.PIPELINE_SUCCESS,
    ]


def test_basic_get_logs_for_run_multiple_runs():
    event_log_storage = PostgresEventLogStorage.create_nuked_storage(get_test_conn_string())

    @solid
    def return_one(_):
        return 1

    def _solids():
        return_one()  # pylint: disable=no-value-for-parameter

    events_one, result_one = gather_events(_solids)
    for event in events_one:
        event_log_storage.store_event(event)

    events_two, result_two = gather_events(_solids)
    for event in events_two:
        event_log_storage.store_event(event)

    out_events_one = event_log_storage.get_logs_for_run(result_one.run_id)
    assert len(out_events_one) == 7

    assert event_types(out_events_one) == [
        DagsterEventType.PIPELINE_START,
        DagsterEventType.ENGINE_EVENT,
        DagsterEventType.STEP_START,
        DagsterEventType.STEP_OUTPUT,
        DagsterEventType.STEP_SUCCESS,
        DagsterEventType.ENGINE_EVENT,
        DagsterEventType.PIPELINE_SUCCESS,
    ]

    assert set(map(lambda e: e.run_id, out_events_one)) == {result_one.run_id}

    out_events_two = event_log_storage.get_logs_for_run(result_two.run_id)
    assert len(out_events_two) == 7

    assert event_types(out_events_two) == [
        DagsterEventType.STEP_OUTPUT,
        DagsterEventType.PIPELINE_START,
        DagsterEventType.ENGINE_EVENT,
        DagsterEventType.STEP_START,
        DagsterEventType.STEP_SUCCESS,
        DagsterEventType.ENGINE_EVENT,
        DagsterEventType.PIPELINE_SUCCESS,
    ]

    assert set(map(lambda e: e.run_id, out_events_two)) == {result_two.run_id}


def test_basic_get_logs_for_run_multiple_runs_cursors():
    event_log_storage = PostgresEventLogStorage.create_nuked_storage(get_test_conn_string())

    @solid
    def return_one(_):
        return 1

    def _solids():
        return_one()  # pylint: disable=no-value-for-parameter

    events_one, result_one = gather_events(_solids)
    for event in events_one:
        event_log_storage.store_event(event)

    events_two, result_two = gather_events(_solids)
    for event in events_two:
        event_log_storage.store_event(event)

    out_events_one = event_log_storage.get_logs_for_run(result_one.run_id, cursor=1)
    assert len(out_events_one) == 5

    assert event_types(out_events_one) == [
        # DagsterEventType.PIPELINE_START,
        # DagsterEventType.ENGINE_EVENT,
        DagsterEventType.STEP_START,
        DagsterEventType.STEP_OUTPUT,
        DagsterEventType.STEP_SUCCESS,
        DagsterEventType.ENGINE_EVENT,
        DagsterEventType.PIPELINE_SUCCESS,
    ]

    assert set(map(lambda e: e.run_id, out_events_one)) == {result_one.run_id}

    out_events_two = event_log_storage.get_logs_for_run(result_two.run_id, cursor=2)
    assert len(out_events_two) == 4

    assert event_types(out_events_two) == [
        # DagsterEventType.PIPELINE_START,
        # DagsterEventType.ENGINE_EVENT,
        # DagsterEventType.STEP_OUTPUT,
        DagsterEventType.STEP_START,
        DagsterEventType.STEP_SUCCESS,
        DagsterEventType.ENGINE_EVENT,
        DagsterEventType.PIPELINE_SUCCESS,
    ]

    assert set(map(lambda e: e.run_id, out_events_two)) == {result_two.run_id}


def test_listen_notify_single_run_event():
    event_log_storage = PostgresEventLogStorage.create_nuked_storage(get_test_conn_string())

    @solid
    def return_one(_):
        return 1

    def _solids():
        return_one()  # pylint: disable=no-value-for-parameter

    event_watcher = create_event_watcher(get_test_conn_string())

    run_id = str(uuid.uuid4())

    event_watcher.watch_run(run_id)

    try:
        events, result = gather_events(_solids, run_config=RunConfig(run_id=run_id))
        for event in events:
            event_log_storage.store_event(event)

        event = event_watcher.queue.get(block=True)

        assert isinstance(event, EventWatcherStart)

        for _ in range(0, 5):
            watcher_event = event_watcher.queue.get(block=True)
            assert isinstance(watcher_event, EventWatcherEvent)
            assert watcher_event.payload.run_id == result.run_id

    finally:
        event_watcher.close()


def test_listen_notify_filter_two_runs_event():
    event_log_storage = PostgresEventLogStorage.create_nuked_storage(get_test_conn_string())

    @solid
    def return_one(_):
        return 1

    def _solids():
        return_one()  # pylint: disable=no-value-for-parameter

    event_watcher = create_event_watcher(get_test_conn_string())

    run_id_one = str(uuid.uuid4())
    run_id_two = str(uuid.uuid4())

    event_watcher.watch_run(run_id_one)
    event_watcher.watch_run(run_id_two)

    try:
        events_one, result_one = gather_events(_solids, run_config=RunConfig(run_id=run_id_one))
        for event in events_one:
            event_log_storage.store_event(event)

        events_two, result_two = gather_events(_solids, run_config=RunConfig(run_id=run_id_two))
        for event in events_two:
            event_log_storage.store_event(event)

        event = event_watcher.queue.get(block=True)

        assert isinstance(event, EventWatcherStart)

        for _ in range(0, 10):
            watcher_event = event_watcher.queue.get(block=True)
            assert isinstance(watcher_event, EventWatcherEvent)
            assert watcher_event.payload.run_id in {result_one.run_id, result_two.run_id}

    finally:
        event_watcher.close()


def test_listen_notify_filter_run_event():
    event_log_storage = PostgresEventLogStorage.create_nuked_storage(get_test_conn_string())

    @solid
    def return_one(_):
        return 1

    def _solids():
        return_one()  # pylint: disable=no-value-for-parameter

    event_watcher = create_event_watcher(get_test_conn_string())

    run_id_one = str(uuid.uuid4())
    run_id_two = str(uuid.uuid4())

    # only watch one of the runs
    event_watcher.watch_run(run_id_two)

    try:
        events_one, _result_one = gather_events(_solids, run_config=RunConfig(run_id=run_id_one))
        for event in events_one:
            event_log_storage.store_event(event)

        events_two, result_two = gather_events(_solids, run_config=RunConfig(run_id=run_id_two))
        for event in events_two:
            event_log_storage.store_event(event)

        event = event_watcher.queue.get(block=True)

        assert isinstance(event, EventWatcherStart)

        for _ in range(0, 5):
            watcher_event = event_watcher.queue.get(block=True)
            assert isinstance(watcher_event, EventWatcherEvent)
            assert watcher_event.payload.run_id == result_two.run_id

    finally:
        event_watcher.close()
