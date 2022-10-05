import threading
from typing import Any, Callable, List

import dagster._check as check
from dagster._core.events import DagsterEventType
from dagster._core.events.log import EventLogEntry
from dagster._daemon.auto_run_reexecution.event_log_consumer import (
    _EVENT_LOG_FETCH_LIMIT,
    get_new_cursor,
)

from .sql_event_log import SqlEventLogStorage

POLLING_CADENCE = 0.1  # 100 ms


class SqlPollingAssetEventWatcher:
    def __init__(self, event_log_storage: SqlEventLogStorage):
        self._event_log_storage = check.inst_param(
            event_log_storage, "event_log_storage", SqlEventLogStorage
        )
        self._watching_lock: threading.Lock = threading.Lock()
        self._thread = None
        self._disposed = False

    def watch(self, callback: Callable[[EventLogEntry], Any]):
        if self._disposed:
            return
        callback = check.callable_param(callback, "callback")
        with self._watching_lock:
            if not self._thread or self._thread.should_thread_exit.is_set():
                self._thread = SqlPollingAssetEventWatcherThread(self._event_log_storage)
                self._thread.daemon = True
                self._thread.start()
            self._thread.add_callback(callback)

    def unwatch(self, callback: Callable[[EventLogEntry], Any]):
        callback = check.callable_param(callback, "callback")
        with self._watching_lock:
            self._thread.remove_callback(callback)

    def __del__(self):
        self.close()

    def close(self):
        if not self._disposed:
            self._disposed = True
            with self._watching_lock:
                if not self._thread.should_thread_exit.is_set():
                    self._thread.should_thread_exit.set()
                self._thread = None


class SqlPollingAssetEventWatcherThread(threading.Thread):
    """subclass of Thread that watches for new Events by polling every POLLING_CADENCE

    Holds a list of callbacks (_callback_fn_list) each passed in by an `Observer`. Note that
        the callbacks have a cursor associated; this means that the callbacks should be
        only executed on EventLogEntrys with an associated id >= callback.cursor
    Exits when `self.should_thread_exit` is set.

    LOCKING INFO:
        INVARIANTS: _callback_fn_list_lock protects _callback_fn_list

    """

    def __init__(self, event_log_storage: SqlEventLogStorage):
        super(SqlPollingAssetEventWatcherThread, self).__init__()
        self._event_log_storage = check.inst_param(
            event_log_storage, "event_log_storage", SqlEventLogStorage
        )
        self._callback_fn_list_lock: threading.Lock = threading.Lock()
        self._callback_fn_list: List[Callable] = []
        self._should_thread_exit = threading.Event()
        self.name = "mysql-event-watch-assets"

    @property
    def should_thread_exit(self) -> threading.Event:
        return self._should_thread_exit

    def add_callback(self, callback: Callable[[EventLogEntry], Any]):
        """Observer has started watching this run.
            Add a callback to execute on new EventLogEntrys after the given cursor

        Args:
            cursor (Optional[str]): event log cursor for the callback to execute
            callback (Callable[[EventLogEntry, str], None]): callback to update the Dagster UI
        """
        callback = check.callable_param(callback, "callback")
        with self._callback_fn_list_lock:
            self._callback_fn_list.append(callback)

    def remove_callback(self, callback: Callable[[EventLogEntry], Any]):
        """Observer has stopped watching this run;
            Remove a callback from the list of callbacks to execute on new EventLogEntrys

            Also kill thread if no callbacks remaining

        Args:
            callback (Callable[[EventLogEntry, str], None]): callback to remove from list of callbacks
        """
        callback = check.callable_param(callback, "callback")
        with self._callback_fn_list_lock:
            self._callback_fn_list.remove(callback)
            if not self._callback_fn_list:
                self._should_thread_exit.set()

    def run(self):
        """Polling function to update Observers with EventLogEntrys from Event Log DB.
        Wakes every POLLING_CADENCE &
            1. executes a SELECT query to get new EventLogEntrys
            2. fires each callback (taking into account the callback.cursor) on the new EventLogEntrys
        Uses max_index_so_far as a cursor in the DB to make sure that only new records are retrieved
        """
        cursor = self._event_log_storage.get_maximum_record_id()

        while not self._should_thread_exit.wait(POLLING_CADENCE):
            events_by_log_id_for_type = self._event_log_storage.get_logs_for_all_runs_by_log_id(
                after_cursor=-1 if cursor == None else cursor,
                dagster_event_type={
                    DagsterEventType.ASSET_MATERIALIZATION,
                    DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
                    DagsterEventType.ASSET_OBSERVATION,
                    DagsterEventType.STEP_START,
                    DagsterEventType.STEP_FAILURE,
                },
                limit=1 if cursor == None else _EVENT_LOG_FETCH_LIMIT,
            )

            events = list(events_by_log_id_for_type.values())
            if len(events):
                with self._callback_fn_list_lock:
                    for callback in self._callback_fn_list:
                        callback(events)

            cursor = get_new_cursor(
                cursor,
                self._event_log_storage.get_maximum_record_id(),
                _EVENT_LOG_FETCH_LIMIT,
                list(events_by_log_id_for_type.keys()),
            )
