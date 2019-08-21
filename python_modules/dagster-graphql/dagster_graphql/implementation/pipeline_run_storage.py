import atexit

import gevent
import gevent.lock

from dagster.core.storage.event_log import EventLogSequence


class PipelineRunObservableSubscribe(object):
    def __init__(self, pipeline_run, after_cursor=None):
        self.event_log_sequence = EventLogSequence()
        self.pipeline_run = pipeline_run
        self.observer = None
        self.after_cursor = after_cursor or -1
        self.lock = gevent.lock.Semaphore()
        self.flush_scheduled = False
        self.flush_after = 0.75
        atexit.register(self._cleanup)

    def __call__(self, observer):
        self.observer = observer
        events = self.pipeline_run.logs_after(self.after_cursor)
        if events:
            self.observer.on_next(events)
        self.pipeline_run.subscribe(self)

    def handle_new_event(self, new_event):
        with self.lock:
            self.event_log_sequence = self.event_log_sequence.append(new_event)

            if self.flush_after is None:
                self.observer.on_next(self.event_log_sequence)
                self.event_log_sequence = EventLogSequence()
                return

            if not self.flush_scheduled:
                self.flush_scheduled = True
                gevent.spawn(self._flush_logs_after_delay)

    def _flush_logs_after_delay(self):
        gevent.sleep(self.flush_after)
        with self.lock:
            self.observer.on_next(self.event_log_sequence)
            self.event_log_sequence = EventLogSequence()
            self.flush_scheduled = False

    def _cleanup(self):
        # Make incoming logs flush immediately to ensure we communciate failures
        # to client on unexpected exit
        self.flush_after = None
