import time
import copy
from collections import OrderedDict
from enum import Enum
import gevent
import gevent.lock
import logging
from rx import Observable
from dagster import check
from dagster.utils.logging import StructuredLoggerMessage
from dagster.core.events import (
    EventRecord,
    PipelineEventRecord,
    EventType,
)


class PipelineRunStatus(Enum):
    NOT_STARTED = 'NOT_STARTED'
    STARTED = 'STARTED'
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'


class PipelineRunStorage(object):
    def __init__(self, pipeline_run_implementation=None):
        self._runs = OrderedDict()
        if not pipeline_run_implementation:
            pipeline_run_implementation = InMemoryPipelineRun
        self._pipeline_run_implementation = pipeline_run_implementation

    def add_run(self, pipeline_run):
        check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
        self._runs[pipeline_run.run_id] = pipeline_run

    def all_runs(self):
        return self._runs.values()

    def all_runs_for_pipeline(self, pipeline_name):
        return [r for r in self.all_runs() if r.pipeline_name == pipeline_name]

    def get_run_by_id(self, id_):
        return self._runs.get(id_)

    def __getitem__(self, id_):
        return self.get_run_by_id(id_)

    def create_run(self, *args, **kwargs):
        return self._pipeline_run_implementation(*args, **kwargs)


class PipelineRun(object):
    def __init__(
        self,
        run_id,
        pipeline_name,
        typed_environment,
        config,
        execution_plan,
        status=PipelineRunStatus.NOT_STARTED,
    ):
        self.__subscribers = []
        self.__debouncing_queue = DebouncingLogQueue()

        self._run_id = run_id
        self._status = PipelineRunStatus.NOT_STARTED
        self._pipeline_name = pipeline_name
        self._config = config
        self._typed_environment = typed_environment
        self._execution_plan = execution_plan

    @property
    def run_id(self):
        return self._run_id

    @property
    def status(self):
        return self._status

    @property
    def pipeline_name(self):
        return self._pipeline_name

    @property
    def typed_environment(self):
        return self._typed_environment

    @property
    def config(self):
        return self._config

    @property
    def execution_plan(self):
        return self._execution_plan

    def logs_after(self, cursor):
        raise NotImplementedError()

    def all_logs(self):
        raise NotImplementedError()

    def store_event(self, new_event):
        raise NotImplementedError()

    def _enqueue_flush_logs(self):
        events = self.__debouncing_queue.attempt_dequeue()

        if events:
            for subscriber in self.__subscribers:
                subscriber.handle_new_events(events)

    def handle_new_event(self, new_event):
        check.inst_param(new_event, 'new_event', EventRecord)

        if new_event.event_type == EventType.PIPELINE_START:
            self._status = PipelineRunStatus.STARTED
        elif new_event.event_type == EventType.PIPELINE_SUCCESS:
            self._status = PipelineRunStatus.SUCCESS
        elif new_event.event_type == EventType.PIPELINE_FAILURE:
            self._status = PipelineRunStatus.FAILURE

        self.store_event(new_event)
        self.__debouncing_queue.enqueue(new_event)
        gevent.spawn(self._enqueue_flush_logs)

    def subscribe(self, subscriber):
        self.__subscribers.append(subscriber)

    def observable_after_cursor(self, cursor=None):
        return Observable.create( # pylint: disable=E1101
            PipelineRunObservableSubscribe(self, cursor),
        )


class InMemoryPipelineRun(PipelineRun):
    def __init__(self, *args, **kwargs):
        super(InMemoryPipelineRun, self).__init__(*args, **kwargs)
        self._logs = []

    def logs_after(self, cursor):
        cursor = int(cursor) + 1
        return self._logs[cursor:]

    def all_logs(self):
        return self._logs

    def store_event(self, new_event):
        self._logs.append(new_event)


class PipelineRunObservableSubscribe(object):
    def __init__(self, pipeline_run, start_cursor=None):
        self.pipeline_run = pipeline_run
        self.observer = None
        self.start_cursor = start_cursor or 0

    def __call__(self, observer):
        self.observer = observer
        events = self.pipeline_run.logs_after(self.start_cursor)
        if events:
            self.observer.on_next(events)
        self.pipeline_run.subscribe(self)

    def handle_new_events(self, events):
        check.list_param(events, 'events', EventRecord)
        self.observer.on_next(events)


class DebouncingLogQueue(object):
    '''
    A queue that debounces dequeuing operation
    '''

    def __init__(self, timeout_length=1.0, sleep_length=0.1):
        self._log_queue_lock = gevent.lock.Semaphore()
        self._log_queue = []
        self._is_dequeueing_blocked = False
        self._queue_timeout = None
        self._timeout_length = check.float_param(timeout_length, 'timeout_length')
        self._sleep_length = check.float_param(sleep_length, 'sleep_length')

    def attempt_dequeue(self):
        '''
        Attempt to dequeue from queue. Will block first call to this until the
        timeout_length has elapsed from last enqueue. Subsequent calls return
        empty list, until the dequeing timeout happens.
        '''
        with self._log_queue_lock:
            if self._is_dequeueing_blocked:
                return []
            else:
                self._is_dequeueing_blocked = True

        # wait till we have elapsed timeout_length seconds from first event, while
        # letting other gevent threads do the work (sleep_length is the chosen sleep cycle)
        while (time.time() - self._queue_timeout) < self._timeout_length:
            gevent.sleep(self._sleep_length)

        with self._log_queue_lock:
            if self._log_queue:
                events = copy.copy(self._log_queue)
                self._log_queue = []
            else:
                events = []
            self._is_dequeueing_blocked = False
            self._queue_timeout = None

        return events

    def enqueue(self, item):
        with self._log_queue_lock:
            if not self._queue_timeout:
                self._queue_timeout = time.time()
            self._log_queue.append(item)
