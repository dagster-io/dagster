import os
from enum import Enum
from threading import Event, Thread
from time import sleep

import dagster._check as check


class State(Enum):
    # initialized
    NULL = 0
    # streaming the existing event log entries
    LOADING = 1
    # watching for new writes
    WATCHING = 2


def get_chunk_size() -> int:
    return int(os.getenv("DAGIT_EVENT_LOAD_CHUNK_SIZE", "10000"))


class PipelineRunObservableSubscribe:
    def __init__(self, instance, run_id, cursor=None):
        self.instance = instance
        self.run_id = run_id
        self.observer = None
        self.state = State.NULL
        self.load_thread = None
        self.stopping = None
        self.stopped = None
        self.cursor = cursor

    def __call__(self, observer):
        self.observer = observer
        check.invariant(self.state is State.NULL, f"unexpected state {self.state}")
        chunk_size = get_chunk_size()
        connection = self.instance.get_records_for_run(self.run_id, self.cursor, limit=chunk_size)
        events = [record.event_log_entry for record in connection.records]
        self.observer.on_next((events, connection.has_more, connection.cursor))
        self.cursor = connection.cursor

        if connection.has_more:
            self.load_events()
        else:
            self.watch_events()

        return self

    def load_events(self):
        self.state = State.LOADING

        self.stopping = Event()
        self.stopped = Event()
        self.load_thread = Thread(
            target=self.background_event_loading,
            args=(sleep,),
            name=f"load-events-{self.run_id}",
        )

        self.load_thread.start()

    def watch_events(self):
        self.state = State.WATCHING
        self.instance.watch_event_logs(self.run_id, self.cursor, self.handle_new_event)

    def background_event_loading(self, sleep_fn):
        chunk_size = get_chunk_size()

        while not self.stopping.is_set():
            connection = self.instance.get_records_for_run(
                self.run_id, self.cursor, limit=chunk_size
            )
            if self.observer is None:
                break

            events = [record.event_log_entry for record in connection.records]
            self.observer.on_next((events, connection.has_more, connection.cursor))
            self.cursor = connection.cursor

            if not connection.has_more:
                break

            sleep_fn(0)

        if not self.stopping.is_set():
            self.watch_events()

        self.stopped.set()
        return

    def dispose(self):
        # called when the connection gets closed, allowing the observer to get GC'ed
        if self.observer and callable(getattr(self.observer, "dispose", None)):
            self.observer.dispose()
        self.observer = None

        if self.state is State.WATCHING:
            self.instance.end_watch_event_logs(self.run_id, self.handle_new_event)
        elif self.state is State.LOADING:
            self.stopping.set()
            if self.load_thread and self.load_thread.is_alive():
                self.load_thread.join(timeout=5)
                self.load_thread = None

    def handle_new_event(self, new_event, cursor):
        if self.observer:
            self.observer.on_next(([new_event], False, cursor))
