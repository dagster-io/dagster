import threading
from typing import Callable, List, MutableMapping, NamedTuple

import dagster._check as check
from dagster.core.events.log import EventLogEntry

from .sql_event_log import SqlEventLogStorage

POLLING_CADENCE = 0.1  # 100 ms


class CallbackAfterCursor(NamedTuple):
    """Callback passed from Observer class in event polling

    start_cursor (int): Only process EventLogEntrys with an id >= start_cursor
        (earlier ones have presumably already been processed)
    callback (Callable[[EventLogEntry], None]): callback passed from Observer
        to call on new EventLogEntrys
    """

    start_cursor: int
    callback: Callable[[EventLogEntry], None]


class SqlPollingEventWatcher:
    """Event Log Watcher that uses a multithreaded polling approach to retrieving new events for run_ids
    This class' job is to manage a collection of threads that each poll the event log for a given run_id
    Uses one thread (SqlPollingRunIdEventWatcherThread) per watched run_id

    LOCKING INFO:
        ORDER: _dict_lock -> run_id_thread.callback_fn_list_lock
        INVARIANTS: _dict_lock protects _run_id_to_watcher_dict
    """

    def __init__(self, event_log_storage: SqlEventLogStorage):
        self._event_log_storage = check.inst_param(
            event_log_storage, "event_log_storage", SqlEventLogStorage
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

    def watch_run(self, run_id: str, start_cursor: int, callback: Callable[[EventLogEntry], None]):
        run_id = check.str_param(run_id, "run_id")
        start_cursor = check.int_param(start_cursor, "start_cursor")
        callback = check.callable_param(callback, "callback")
        with self._dict_lock:
            if run_id not in self._run_id_to_watcher_dict:
                self._run_id_to_watcher_dict[run_id] = SqlPollingRunIdEventWatcherThread(
                    self._event_log_storage, run_id
                )
                self._run_id_to_watcher_dict[run_id].daemon = True
                self._run_id_to_watcher_dict[run_id].start()
            self._run_id_to_watcher_dict[run_id].add_callback(start_cursor, callback)

    def unwatch_run(self, run_id: str, handler: Callable[[EventLogEntry], None]):
        run_id = check.str_param(run_id, "run_id")
        handler = check.callable_param(handler, "handler")
        with self._dict_lock:
            if run_id in self._run_id_to_watcher_dict:
                self._run_id_to_watcher_dict[run_id].remove_callback(handler)
                if self._run_id_to_watcher_dict[run_id].should_thread_exit.is_set():
                    del self._run_id_to_watcher_dict[run_id]

    def __del__(self):
        self.close()

    def close(self):
        if not self._disposed:
            self._disposed = True
            with self._dict_lock:
                for watcher_thread in self._run_id_to_watcher_dict.values():
                    if not watcher_thread.should_thread_exit.is_set():
                        watcher_thread.should_thread_exit.set()
                for run_id in self._run_id_to_watcher_dict:
                    self._run_id_to_watcher_dict[run_id].join()
                del self._run_id_to_watcher_dict


class SqlPollingRunIdEventWatcherThread(threading.Thread):
    """subclass of Thread that watches a given run_id for new Events by polling every POLLING_CADENCE

    Holds a list of callbacks (_callback_fn_list) each passed in by an `Observer`. Note that
        the callbacks have a cursor associated; this means that the callbacks should be
        only executed on EventLogEntrys with an associated id >= callback.start_cursor
    Exits when `self.should_thread_exit` is set.

    LOCKING INFO:
        INVARIANTS: _callback_fn_list_lock protects _callback_fn_list

    """

    def __init__(self, event_log_storage: SqlEventLogStorage, run_id: str):
        super(SqlPollingRunIdEventWatcherThread, self).__init__()
        self._event_log_storage = check.inst_param(
            event_log_storage, "event_log_storage", SqlEventLogStorage
        )
        self._run_id = check.str_param(run_id, "run_id")
        self._callback_fn_list_lock: threading.Lock = threading.Lock()
        self._callback_fn_list: List[CallbackAfterCursor] = []
        self._should_thread_exit = threading.Event()
        self.name = f"mysql-event-watch-run-id-{self._run_id}"

    @property
    def should_thread_exit(self) -> threading.Event:
        return self._should_thread_exit

    def add_callback(self, start_cursor: int, callback: Callable[[EventLogEntry], None]):
        """Observer has started watching this run.
            Add a callback to execute on new EventLogEntrys st. id >= start_cursor

        Args:
            start_cursor (int): minimum event_id for the callback to execute
            callback (Callable[[EventLogEntry], None]): callback to update the Dagster UI
        """
        start_cursor = check.int_param(start_cursor, "start_cursor")
        callback = check.callable_param(callback, "callback")
        with self._callback_fn_list_lock:
            self._callback_fn_list.append(CallbackAfterCursor(start_cursor, callback))

    def remove_callback(self, callback: Callable[[EventLogEntry], None]):
        """Observer has stopped watching this run;
            Remove a callback from the list of callbacks to execute on new EventLogEntrys

            Also kill thread if no callbacks remaining (i.e. no Observers are watching this run_id)

        Args:
            callback (Callable[[EventLogEntry], None]): callback to remove from list of callbacks
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

    def run(self):
        """Polling function to update Observers with EventLogEntrys from Event Log DB.
        Wakes every POLLING_CADENCE &
            1. executes a SELECT query to get new EventLogEntrys
            2. fires each callback (taking into account the callback.cursor) on the new EventLogEntrys
        Uses max_index_so_far as a cursor in the DB to make sure that only new records are retrieved
        """
        cursor = -1
        while not self._should_thread_exit.wait(POLLING_CADENCE):
            events = self._event_log_storage.get_logs_for_run(self._run_id, cursor=cursor)
            for event_record in events:
                cursor += 1
                with self._callback_fn_list_lock:
                    for callback_with_cursor in self._callback_fn_list:
                        if callback_with_cursor.start_cursor < cursor:
                            callback_with_cursor.callback(event_record)
