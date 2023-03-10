import logging
import time

from dagster import DagsterEvent, DagsterEventType, EventLogEntry
from dagster._core.instance import DagsterInstance
from dagster._core.test_utils import create_run_for_test
from dagster._daemon.auto_run_reexecution.event_log_consumer import (
    EventLogConsumerDaemon,
    get_new_cursor,
)

TEST_EVENT_LOG_FETCH_LIMIT = 10


class TestEventLogConsumerDaemon(EventLogConsumerDaemon):
    """Override the actual handlers so that we can just test which run records they receive."""

    def __init__(self):
        super(TestEventLogConsumerDaemon, self).__init__(
            event_log_fetch_limit=TEST_EVENT_LOG_FETCH_LIMIT
        )
        self.run_records = []

    @property
    def handle_updated_runs_fns(self):
        def stash_run_records(_ctx, run_records):
            self.run_records = run_records
            yield

        return [stash_run_records]


def _create_success_event(instance, run):
    dagster_event = DagsterEvent(
        event_type_value=DagsterEventType.RUN_SUCCESS.value,
        pipeline_name="foo",
        message="yay success",
    )
    event_record = EventLogEntry(
        user_message="",
        level=logging.INFO,
        pipeline_name="foo",
        run_id=run.run_id,
        error_info=None,
        timestamp=time.time(),
        dagster_event=dagster_event,
    )

    instance.handle_new_event(event_record)


def test_daemon(instance: DagsterInstance, empty_workspace_context):
    daemon = TestEventLogConsumerDaemon()

    list(daemon.run_iteration(empty_workspace_context))
    assert daemon.run_records == []

    run = create_run_for_test(instance, "test_pipeline")
    instance.report_run_failed(run)

    list(daemon.run_iteration(empty_workspace_context))
    assert [record.dagster_run.run_id for record in daemon.run_records] == [run.run_id]

    # not called again for same event
    daemon.run_records = []  # reset this since it will keep the value from the last call
    list(daemon.run_iteration(empty_workspace_context))
    assert daemon.run_records == []


def test_events_exceed_limit(instance: DagsterInstance, empty_workspace_context):
    daemon = TestEventLogConsumerDaemon()
    list(daemon.run_iteration(empty_workspace_context))

    for _ in range(TEST_EVENT_LOG_FETCH_LIMIT + 1):
        run = create_run_for_test(instance, "test_pipeline")
        instance.report_run_failed(run)

    list(daemon.run_iteration(empty_workspace_context))
    assert len(daemon.run_records) == TEST_EVENT_LOG_FETCH_LIMIT

    list(daemon.run_iteration(empty_workspace_context))
    assert len(daemon.run_records) == 1


def test_success_and_failure_events(instance: DagsterInstance, empty_workspace_context):
    daemon = TestEventLogConsumerDaemon()
    list(daemon.run_iteration(empty_workspace_context))

    for _ in range(TEST_EVENT_LOG_FETCH_LIMIT + 1):
        run = create_run_for_test(instance, "foo")
        instance.report_run_failed(run)

        run = create_run_for_test(instance, "foo")
        _create_success_event(instance, run)

    list(daemon.run_iteration(empty_workspace_context))
    assert len(daemon.run_records) == TEST_EVENT_LOG_FETCH_LIMIT * 2

    list(daemon.run_iteration(empty_workspace_context))
    assert len(daemon.run_records) == 2


FAILURE_KEY = "EVENT_LOG_CONSUMER_CURSOR-PIPELINE_FAILURE"
SUCCESS_KEY = "EVENT_LOG_CONSUMER_CURSOR-PIPELINE_SUCCESS"


def test_cursors(instance: DagsterInstance, empty_workspace_context):
    assert instance.run_storage.kvs_get({FAILURE_KEY, SUCCESS_KEY}) == {}

    daemon = TestEventLogConsumerDaemon()
    list(daemon.run_iteration(empty_workspace_context))

    assert instance.run_storage.kvs_get({FAILURE_KEY, SUCCESS_KEY}) == {
        FAILURE_KEY: str(0),
        SUCCESS_KEY: str(0),
    }

    run1 = create_run_for_test(instance, "foo")
    run2 = create_run_for_test(instance, "foo")

    instance.report_run_failed(run1)
    instance.report_run_failed(run2)

    list(daemon.run_iteration(empty_workspace_context))
    assert len(daemon.run_records) == 2

    cursors = instance.run_storage.kvs_get({FAILURE_KEY, SUCCESS_KEY})

    list(daemon.run_iteration(empty_workspace_context))
    assert instance.run_storage.kvs_get({FAILURE_KEY, SUCCESS_KEY}) == cursors

    for _ in range(5):
        instance.report_engine_event("foo", run1)
        instance.report_engine_event("foo", run2)

    list(daemon.run_iteration(empty_workspace_context))
    assert instance.run_storage.kvs_get({FAILURE_KEY, SUCCESS_KEY}) == {
        FAILURE_KEY: str(int(cursors[FAILURE_KEY]) + 10),
        SUCCESS_KEY: str(int(cursors[SUCCESS_KEY]) + 10),
    }

    run3 = create_run_for_test(instance, "foo")
    run4 = create_run_for_test(instance, "foo")

    instance.report_run_failed(run3)
    instance.report_run_failed(run4)

    list(daemon.run_iteration(empty_workspace_context))
    assert len(daemon.run_records) == 2


def test_cursor_init(instance: DagsterInstance, empty_workspace_context):
    instance.run_storage.wipe()
    daemon = TestEventLogConsumerDaemon()

    run1 = create_run_for_test(instance, "foo")
    run2 = create_run_for_test(instance, "foo")

    instance.report_run_failed(run1)
    instance.report_run_failed(run2)

    list(daemon.run_iteration(empty_workspace_context))
    assert len(daemon.run_records) == 0, "Cursors init to latest event"

    run3 = create_run_for_test(instance, "foo")
    instance.report_run_failed(run3)

    list(daemon.run_iteration(empty_workspace_context))
    assert len(daemon.run_records) == 1


def test_get_new_cursor():
    # hit fetch limit, uses max new_event_ids
    assert get_new_cursor(0, 20, 8, [3, 4, 5, 6, 7, 8, 9, 10]) == 10

    # hit fetch limit, uses max new_event_ids with overall_max_event_id low
    assert get_new_cursor(0, 7, 8, [3, 4, 5, 6, 7, 8, 9, 10]) == 10

    # didn't hit fetch limit, uses max new_event_ids with overall_max_event_id low
    assert get_new_cursor(0, 7, 8, [3, 4, 5, 6, 7, 8, 9]) == 9

    # didn't hit fetch limit, jumps to overall_max_event_id
    assert get_new_cursor(0, 20, 4, [1, 2, 3]) == 20

    # empty event log
    assert get_new_cursor(0, None, 4, []) == 0

    # empty overall_max_event_id
    assert get_new_cursor(0, None, 5, [2, 3, 4]) == 4

    # no new_event_ids
    assert get_new_cursor(0, 10, 4, []) == 10
