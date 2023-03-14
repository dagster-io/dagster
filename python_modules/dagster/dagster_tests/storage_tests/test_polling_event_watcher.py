import tempfile
import time
from contextlib import contextmanager
from typing import Any, Callable, Mapping, Union

import dagster._check as check
from dagster._core.events import DagsterEvent, DagsterEventType, EngineEventData
from dagster._core.events.log import EventLogEntry
from dagster._core.storage.event_log import SqliteEventLogStorage, SqlPollingEventWatcher
from dagster._core.storage.event_log.base import EventLogCursor
from dagster._serdes.config_class import ConfigurableClassData
from typing_extensions import Self


class SqlitePollingEventLogStorage(SqliteEventLogStorage):
    """SQLite-backed event log storage that uses SqlPollingEventWatcher for watching runs.

    This class is a subclass of SqliteEventLogStorage that uses the SqlPollingEventWatcher class
    (polling via SELECT queries) instead of the SqliteEventLogStorageWatchdog (filesystem watcher) to
    observe runs.
    """

    def __init__(self, *args, **kwargs):
        super(SqlitePollingEventLogStorage, self).__init__(*args, **kwargs)
        self._watcher = SqlPollingEventWatcher(self)
        self._disposed = False

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]
    ) -> Self:
        return SqlitePollingEventLogStorage(inst_data=inst_data, **config_value)

    def watch(
        self, run_id: str, cursor: Union[str, int], callback: Callable[[EventLogEntry], None]
    ):
        check.str_param(run_id, "run_id")
        check.opt_str_param(cursor, "cursor")
        check.callable_param(callback, "callback")
        self._watcher.watch_run(run_id, cursor, callback)

    def end_watch(self, run_id: str, handler: Callable[[EventLogEntry], None]):
        check.str_param(run_id, "run_id")
        check.callable_param(handler, "handler")
        self._watcher.unwatch_run(run_id, handler)

    def __del__(self):
        self.dispose()

    def dispose(self):
        if not self._disposed:
            self._disposed = True
            self._watcher.close()


RUN_ID = "foo"


def create_event(count: int, run_id: str = RUN_ID):
    return EventLogEntry(
        error_info=None,
        user_message=str(count),
        level="debug",
        run_id=run_id,
        timestamp=time.time(),
        dagster_event=DagsterEvent(
            DagsterEventType.ENGINE_EVENT.value,
            "nonce",
            event_specific_data=EngineEventData.in_process(999),
        ),
    )


@contextmanager
def create_sqlite_run_event_logstorage():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        yield SqlitePollingEventLogStorage(tmpdir_path)


def test_using_logstorage():
    with create_sqlite_run_event_logstorage() as storage:
        watched_1 = []
        watched_2 = []

        def watch_one(event, _cursor):
            watched_1.append(event)

        def watch_two(event, _cursor):
            watched_2.append(event)

        assert len(storage.get_logs_for_run(RUN_ID)) == 0

        storage.store_event(create_event(1))
        assert len(storage.get_logs_for_run(RUN_ID)) == 1
        assert len(watched_1) == 0

        storage.watch(RUN_ID, str(EventLogCursor.from_storage_id(1)), watch_one)

        storage.store_event(create_event(2))
        storage.store_event(create_event(3))

        storage.watch(RUN_ID, str(EventLogCursor.from_storage_id(3)), watch_two)
        storage.store_event(create_event(4))

        attempts = 10
        while (len(watched_1) < 3 or len(watched_2) < 1) and attempts > 0:
            time.sleep(0.1)
            attempts -= 1

        assert len(storage.get_logs_for_run(RUN_ID)) == 4
        assert len(watched_1) == 3
        assert len(watched_2) == 1

        storage.end_watch(RUN_ID, watch_one)
        time.sleep(0.3)  # this value scientifically selected from a range of attractive values
        storage.store_event(create_event(5))

        attempts = 10
        while len(watched_2) < 2 and attempts > 0:
            time.sleep(0.1)
            attempts -= 1
        storage.end_watch(RUN_ID, watch_two)

        assert len(storage.get_logs_for_run(RUN_ID)) == 5
        assert len(watched_1) == 3
        assert len(watched_2) == 2

        storage.delete_events(RUN_ID)

        assert len(storage.get_logs_for_run(RUN_ID)) == 0
        assert len(watched_1) == 3
        assert len(watched_2) == 2

        assert [int(evt.message) for evt in watched_1] == [2, 3, 4]
        assert [int(evt.message) for evt in watched_2] == [4, 5]
