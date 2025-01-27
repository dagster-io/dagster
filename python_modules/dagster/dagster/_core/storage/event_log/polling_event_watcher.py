import os
import threading
from typing import TYPE_CHECKING, Callable, NamedTuple, Optional

import dagster._check as check
from dagster._core.events.log import EventLogEntry
from dagster._core.storage.event_log.base import EventLogCursor, EventLogStorage

if TYPE_CHECKING:
    from collections.abc import MutableMapping

INIT_POLL_PERIOD = 0.250  # 250ms
MAX_POLL_PERIOD = 16.0  # 16s


class CallbackAfterCursor(NamedTuple):
    """Callback passed from Observer class in event polling.

    cursor (str): Only process EventLogEntrys after the given cursor
    callback (Callable[[EventLogEntry], None]): callback passed from Observer
        to call on new EventLogEntrys, with a string cursor
    """

    cursor: Optional[str]
    callback: Callable[[EventLogEntry, str], None]


class SqlPollingEventWatcher:
    """Event Log Watcher that uses a multithreaded polling approach to retrieving new events for run_ids
    This class' job is to manage a collection of threads that each poll the event log for a given run_id
    Uses one thread (SqlPollingRunIdEventWatcherThread) per watched run_id.

    LOCKING INFO:
        ORDER: _dict_lock -> run_id_thread.callback_fn_list_lock
        INVARIANTS: _dict_lock protects _run_id_to_watcher_dict
    """

    def __init__(self, event_log_storage: EventLogStorage):
        self._event_log_storage = check.inst_param(
            event_log_storage, "event_log_storage", EventLogStorage
        )

        # INVARIANT: dict_lock protects _run_id_to_watcher_dict
        self._dict_lock: threading.Lock = threading.Lock()
        self._run_id_to_watcher_dict: MutableMapping[str, SqlPollingRunIdEventWatcherThread] = {}
        self._disposed = False

    def has_run_id(self, run_id: str) -> bool:
        run_id = check.str_param(run_id, "run_id")
        with self._dict_lock:
            _has_run_id = run_id in self._run_id_to_watcher_dict
        return _has_run_id

    def watch_run(
        self,
        run_id: str,
        cursor: Optional[str],
        callback: Callable[[EventLogEntry, str], None],
    ) -> None:
        run_id = check.str_param(run_id, "run_id")
        cursor = check.opt_str_param(cursor, "cursor")
        callback = check.callable_param(callback, "callback")
        check.invariant(not self._disposed, "Attempted to watch_run after close")

        with self._dict_lock:
            if run_id not in self._run_id_to_watcher_dict:
                self._run_id_to_watcher_dict[run_id] = SqlPollingRunIdEventWatcherThread(
                    self._event_log_storage, run_id
                )
                self._run_id_to_watcher_dict[run_id].daemon = True
                self._run_id_to_watcher_dict[run_id].start()
            self._run_id_to_watcher_dict[run_id].add_callback(cursor, callback)

    def unwatch_run(
        self,
        run_id: str,
        handler: Callable[[EventLogEntry, str], None],
    ) -> None:
        run_id = check.str_param(run_id, "run_id")
        handler = check.callable_param(handler, "handler")
        with self._dict_lock:
            if run_id in self._run_id_to_watcher_dict:
                self._run_id_to_watcher_dict[run_id].remove_callback(handler)
                if self._run_id_to_watcher_dict[run_id].should_thread_exit.is_set():
                    del self._run_id_to_watcher_dict[run_id]

    def close(self) -> None:
        if not self._disposed:
            self._disposed = True
            with self._dict_lock:
                for watcher_thread in self._run_id_to_watcher_dict.values():
                    if not watcher_thread.should_thread_exit.is_set():
                        watcher_thread.should_thread_exit.set()
                for run_id in self._run_id_to_watcher_dict:
                    self._run_id_to_watcher_dict[run_id].join()
                self._run_id_to_watcher_dict = {}


class SqlPollingRunIdEventWatcherThread(threading.Thread):
    """subclass of Thread that watches a given run_id for new Events by polling every POLLING_CADENCE.

    Holds a list of callbacks (_callback_fn_list) each passed in by an `Observer`. Note that
        the callbacks have a cursor associated; this means that the callbacks should be
        only executed on EventLogEntrys with an associated id >= callback.cursor
    Exits when `self.should_thread_exit` is set.

    LOCKING INFO:
        INVARIANTS: _callback_fn_list_lock protects _callback_fn_list

    """

    def __init__(self, event_log_storage: EventLogStorage, run_id: str):
        super().__init__()
        self._event_log_storage = check.inst_param(
            event_log_storage, "event_log_storage", EventLogStorage
        )
        self._run_id = check.str_param(run_id, "run_id")
        self._callback_fn_list_lock: threading.Lock = threading.Lock()
        self._callback_fn_list: list[CallbackAfterCursor] = []
        self._should_thread_exit = threading.Event()
        self.name = f"sql-event-watch-run-id-{self._run_id}"

    @property
    def should_thread_exit(self) -> threading.Event:
        return self._should_thread_exit

    def add_callback(self, cursor: Optional[str], callback: Callable[[EventLogEntry, str], None]):
        """Observer has started watching this run.
            Add a callback to execute on new EventLogEntrys after the given cursor.

        Args:
            cursor (Optional[str]): event log cursor for the callback to execute
            callback (Callable[[EventLogEntry, str], None]): callback to update the Dagster UI
        """
        cursor = check.opt_str_param(cursor, "cursor")
        callback = check.callable_param(callback, "callback")
        with self._callback_fn_list_lock:
            self._callback_fn_list.append(CallbackAfterCursor(cursor, callback))

    def remove_callback(self, callback: Callable[[EventLogEntry, str], None]):
        """Observer has stopped watching this run;
            Remove a callback from the list of callbacks to execute on new EventLogEntrys.

            Also kill thread if no callbacks remaining (i.e. no Observers are watching this run_id)

        Args:
            callback (Callable[[EventLogEntry, str], None]): callback to remove from list of callbacks
        """
        callback = check.callable_param(callback, "callback")
        with self._callback_fn_list_lock:
            self._callback_fn_list = [
                callback_with_cursor
                for callback_with_cursor in self._callback_fn_list
                if callback_with_cursor.callback != callback
            ]
            if not self._callback_fn_list:
                self._should_thread_exit.set()

    def run(self) -> None:
        """Polling function to update Observers with EventLogEntrys from Event Log DB.
        Wakes every POLLING_CADENCE &
            1. executes a SELECT query to get new EventLogEntrys
            2. fires each callback (taking into account the callback.cursor) on the new EventLogEntrys
        Uses max_index_so_far as a cursor in the DB to make sure that only new records are retrieved.
        """
        cursor = None
        wait_time = INIT_POLL_PERIOD

        chunk_limit = int(os.getenv("DAGSTER_POLLING_EVENT_WATCHER_BATCH_SIZE", "1000"))

        while not self._should_thread_exit.wait(wait_time):
            conn = self._event_log_storage.get_records_for_run(
                self._run_id,
                cursor=cursor,
                limit=chunk_limit,
            )
            cursor = conn.cursor
            for event_record in conn.records:
                with self._callback_fn_list_lock:
                    for callback_with_cursor in self._callback_fn_list:
                        if (
                            callback_with_cursor.cursor is None
                            or EventLogCursor.parse(callback_with_cursor.cursor).storage_id()
                            < event_record.storage_id
                        ):
                            callback_with_cursor.callback(
                                event_record.event_log_entry,
                                str(EventLogCursor.from_storage_id(event_record.storage_id)),
                            )
            wait_time = INIT_POLL_PERIOD if conn.records else min(wait_time * 2, MAX_POLL_PERIOD)
