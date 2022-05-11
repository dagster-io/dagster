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
    def __init__(self, instance, run_id, after_cursor=None):
        self.instance = instance
        self.run_id = run_id
        self.observer = None
        self.state = State.NULL
        self.stopping = None
        self.stopped = None
        self.after_cursor = after_cursor if after_cursor is not None else -1

    def __call__(self, observer):
        self.observer = observer
        check.invariant(self.state is State.NULL, f"unexpected state {self.state}")
        chunk_size = get_chunk_size()
        events = self.instance.logs_after(self.run_id, self.after_cursor, limit=chunk_size)
        done_loading = len(events) < chunk_size

        if events:
            self.observer.on_next((events, not done_loading))
            self.after_cursor = len(events) + int(self.after_cursor)

        if done_loading:
            self.watch_events()
        else:
            self.load_events()

        return self

    def load_events(self):
        self.state = State.LOADING

        self.stopping = Event()
        self.stopped = Event()
        load_thread = Thread(
            target=self.background_event_loading,
            args=(sleep,),
            name=f"load-events-{self.run_id}",
        )

        load_thread.start()

    def watch_events(self):
        self.state = State.WATCHING
        self.instance.watch_event_logs(self.run_id, self.after_cursor, self.handle_new_event)

    def background_event_loading(self, sleep_fn):
        chunk_size = get_chunk_size()

        while not self.stopping.is_set():
            events = self.instance.logs_after(self.run_id, self.after_cursor, limit=chunk_size)
            if self.observer is None:
                break

            done_loading = len(events) < chunk_size

            self.observer.on_next((events, not done_loading))
            self.after_cursor = len(events) + int(self.after_cursor)

            if done_loading:
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

    def handle_new_event(self, new_event):
        if self.observer:
            self.observer.on_next(([new_event], False))
