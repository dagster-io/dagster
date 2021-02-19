import tempfile
import time
from collections import namedtuple
from contextlib import contextmanager
from unittest.mock import Mock

import pytest
from dagster.core.events import DagsterEvent, DagsterEventType, EngineEventData
from dagster.core.events.log import EventRecord
from dagster.core.storage.event_log import SqlEventLogStorage
from dagster.core.test_utils import instance_for_test_tempdir
from dagster_graphql.implementation.pipeline_run_storage import PipelineRunObservableSubscribe
from dagster_tests.core_tests.storage_tests.test_polling_event_watcher import (
    SqlitePollingEventLogStorage,
)


@contextmanager
def create_test_instance_and_storage():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        with instance_for_test_tempdir(
            tmpdir_path,
            overrides={
                "event_log_storage": {
                    "module": "dagster_tests.core_tests.storage_tests.test_polling_event_watcher",
                    "class": "SqlitePollingEventLogStorage",
                    "config": {"base_dir": tmpdir_path},
                }
            },
        ) as instance:
            yield (instance, instance._event_storage)  # pylint: disable=protected-access


RUN_ID = "foo"


class EventStorer:
    def __init__(self, storage: SqlEventLogStorage):
        self._storage = storage
        self._counter = 0

    def store_n_events(self, n: int):
        for _ in range(n):
            self._counter += 1
            self._storage.store_event(self.create_event(self._counter))

    @staticmethod
    def create_event(count: int, run_id: str = RUN_ID):
        return EventRecord(
            None,
            str(count),
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


NumEventsAndCursor = namedtuple("NumEventsAndCursor", ["num_events_before_watch", "after_cursor"])

MAX_NUM_EVENTS_BEFORE_WATCH = 2
MAX_NUM_EVENTS_AFTER_WATCH = 2


@pytest.mark.parametrize(
    "before_watch_config",
    [
        NumEventsAndCursor(num_events_before_watch, after_cursor)
        for num_events_before_watch in range(0, MAX_NUM_EVENTS_BEFORE_WATCH + 1)
        for after_cursor in range(-1, num_events_before_watch + 1)
    ],
)
@pytest.mark.parametrize("num_events_after_watch", list(range(1, MAX_NUM_EVENTS_AFTER_WATCH + 1)))
def test_using_instance(before_watch_config: NumEventsAndCursor, num_events_after_watch: int):
    total_num_events: int = before_watch_config.num_events_before_watch + num_events_after_watch
    with create_test_instance_and_storage() as (instance, storage):
        # set up instance & write `before_watch_config.num_events_before_watch` to event_log
        assert isinstance(storage, SqlitePollingEventLogStorage)
        observable_subscribe = PipelineRunObservableSubscribe(
            instance, RUN_ID, after_cursor=before_watch_config.after_cursor
        )
        event_storer = EventStorer(storage)
        event_storer.store_n_events(before_watch_config.num_events_before_watch)

        # start watching events & write `num_events_after_watch` to event_log
        observable_subscribe(Mock())
        event_storer.store_n_events(num_events_after_watch)
        call_args = observable_subscribe.observer.on_next.call_args_list

        # wait until all events have been captured
        most_recent_event_processed = lambda: int(call_args[-1][0][0][-1].message)
        attempts = 10
        while (
            len(call_args) == 0 or most_recent_event_processed() < total_num_events
        ) and attempts > 0:
            time.sleep(0.1)
            attempts -= 1

        # ensure all expected events captured, no duplicates, etc.
        events_list = [[event_record.message for event_record in call[0][0]] for call in call_args]
        flattened_events_list = [int(message) for lst in events_list for message in lst]
        # PipelineRunObservableSubscribe requests ids > after_cursor + 1
        beginning_cursor = before_watch_config.after_cursor + 2
        assert flattened_events_list == list(
            range(
                beginning_cursor,
                total_num_events + 1,
            )
        )
