import logging
import threading
from collections import defaultdict
from typing import Callable, List, MutableMapping, Optional, Sequence

import dagster._check as check
from dagster._core.events.log import EventLogEntry
from dagster._core.storage.event_log.base import EventLogCursor
from dagster._core.storage.event_log.polling_event_watcher import CallbackAfterCursor

from ..pynotify import await_pg_notifications

POLLING_CADENCE = 0.25


def watcher_thread(
    conn_string: str,
    handlers_dict: MutableMapping[str, Sequence[CallbackAfterCursor]],
    dict_lock: threading.Lock,
    watcher_thread_exit: threading.Event,
    watcher_thread_started: threading.Event,
    channels: Sequence[str],
    gen_event_log_entry_from_cursor: Callable[[int], EventLogEntry],
):
    for notif in await_pg_notifications(
        conn_string,
        channels=channels,
        timeout=POLLING_CADENCE,
        yield_on_timeout=True,
        exit_event=watcher_thread_exit,
        started_event=watcher_thread_started,
    ):
        if notif is None:
            if watcher_thread_exit.is_set():
                break
        else:
            run_id, index_str = notif.payload.split("_")
            with dict_lock:
                if run_id not in handlers_dict:
                    continue

            index = int(index_str)
            with dict_lock:
                handlers = handlers_dict.get(run_id, [])

            dagster_event = gen_event_log_entry_from_cursor(index)

            for callback_with_cursor in handlers:
                try:
                    if (
                        callback_with_cursor.cursor is None
                        or EventLogCursor.parse(callback_with_cursor.cursor).storage_id() < index
                    ):
                        callback_with_cursor.callback(
                            dagster_event, str(EventLogCursor.from_storage_id(index))
                        )
                except:
                    logging.exception("Exception in callback for event watch on run %s.", run_id)


class PostgresEventWatcher:
    def __init__(
        self,
        conn_string: str,
        channels: Sequence[str],
        gen_event_log_entry_from_cursor: Callable[[int], EventLogEntry],
    ):
        self._conn_string: str = check.str_param(conn_string, "conn_string")
        self._handlers_dict: MutableMapping[str, List[CallbackAfterCursor]] = defaultdict(list)
        self._dict_lock: threading.Lock = threading.Lock()
        self._watcher_thread_exit: Optional[threading.Event] = None
        self._watcher_thread_started: Optional[threading.Event] = None
        self._watcher_thread: Optional[threading.Thread] = None
        self._channels: Sequence[str] = check.sequence_param(channels, "channels")
        self._gen_event_log_entry_from_cursor: Callable[
            [int], EventLogEntry
        ] = check.callable_param(gen_event_log_entry_from_cursor, "gen_event_log_entry_from_cursor")

    def watch_run(
        self,
        run_id: str,
        cursor: Optional[str],
        callback: Callable[[EventLogEntry, str], None],
        start_timeout=15,
    ):
        check.str_param(run_id, "run_id")
        check.opt_str_param(cursor, "cursor")
        check.callable_param(callback, "callback")
        if not self._watcher_thread:
            self._watcher_thread_exit = threading.Event()
            self._watcher_thread_started = threading.Event()

            self._watcher_thread = threading.Thread(
                target=watcher_thread,
                args=(
                    self._conn_string,
                    self._handlers_dict,
                    self._dict_lock,
                    self._watcher_thread_exit,
                    self._watcher_thread_started,
                    self._channels,
                    self._gen_event_log_entry_from_cursor,
                ),
                name="postgres-event-watch",
            )
            self._watcher_thread.daemon = True
            self._watcher_thread.start()

            # Wait until the watcher thread is actually listening before returning
            self._watcher_thread_started.wait(start_timeout)
            if not self._watcher_thread_started.is_set():
                raise Exception("Watcher thread never started")

        with self._dict_lock:
            self._handlers_dict[run_id].append(CallbackAfterCursor(cursor, callback))

    def unwatch_run(self, run_id: str, handler: Callable[[EventLogEntry, str], None]):
        check.str_param(run_id, "run_id")
        check.callable_param(handler, "handler")
        with self._dict_lock:
            if run_id in self._handlers_dict:
                self._handlers_dict[run_id] = [
                    callback_with_cursor
                    for callback_with_cursor in self._handlers_dict[run_id]
                    if callback_with_cursor.callback != handler
                ]
                if not self._handlers_dict[run_id]:
                    del self._handlers_dict[run_id]

    def close(self):
        if self._watcher_thread:
            self._watcher_thread_exit.set()
            if self._watcher_thread.is_alive():
                self._watcher_thread.join()
            self._watcher_thread_exit = None
            self._watcher_thread = None
