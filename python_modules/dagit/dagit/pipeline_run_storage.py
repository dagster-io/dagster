from collections import OrderedDict
from enum import Enum
import json
import os
import time

from rx import Observable
import gevent
import gevent.lock
import pyrsistent

from dagster import check
from dagster.core.events import EventRecord, EventType

from dagster.core.execution_plan.objects import ExecutionPlan


class PipelineRunStatus(Enum):
    NOT_STARTED = 'NOT_STARTED'
    STARTED = 'STARTED'
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'


class PipelineRunStorage(object):
    def __init__(self, create_pipeline_run=None):
        self._runs = OrderedDict()
        if not create_pipeline_run:
            create_pipeline_run = InMemoryPipelineRun
        self._create_pipeline_run = create_pipeline_run

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
        return self._create_pipeline_run(*args, **kwargs)


class PipelineRun(object):
    def __init__(self, run_id, pipeline_name, env_config, execution_plan):
        self.__subscribers = []

        self._status = PipelineRunStatus.NOT_STARTED
        self._run_id = check.str_param(run_id, 'run_id')
        self._pipeline_name = check.str_param(pipeline_name, 'pipeline_name')
        self._env_config = check.opt_dict_param(env_config, 'environment_config', key_type=str)
        self._execution_plan = check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)

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
    def config(self):
        return self._env_config

    @property
    def execution_plan(self):
        return self._execution_plan

    def logs_after(self, cursor):
        raise NotImplementedError()

    def all_logs(self):
        raise NotImplementedError()

    def store_event(self, new_event):
        raise NotImplementedError()

    def handle_new_event(self, new_event):
        check.inst_param(new_event, 'new_event', EventRecord)

        if new_event.event_type == EventType.PIPELINE_START:
            self._status = PipelineRunStatus.STARTED
        elif new_event.event_type == EventType.PIPELINE_SUCCESS:
            self._status = PipelineRunStatus.SUCCESS
        elif new_event.event_type == EventType.PIPELINE_FAILURE:
            self._status = PipelineRunStatus.FAILURE

        self.store_event(new_event)
        for subscriber in self.__subscribers:
            subscriber.handle_new_event(new_event)

    def subscribe(self, subscriber):
        self.__subscribers.append(subscriber)

    def observable_after_cursor(self, cursor=None):
        return Observable.create(  # pylint: disable=E1101
            PipelineRunObservableSubscribe(self, cursor)
        )


class InMemoryPipelineRun(PipelineRun):
    def __init__(self, *args, **kwargs):
        super(InMemoryPipelineRun, self).__init__(*args, **kwargs)
        self._log_storage_lock = gevent.lock.Semaphore()
        self._log_sequence = LogSequence()

    def logs_after(self, cursor):
        cursor = int(cursor) + 1
        with self._log_storage_lock:
            return self._log_sequence[cursor:]

    def all_logs(self):
        with self._log_storage_lock:
            return self._log_sequence

    def store_event(self, new_event):
        check.inst_param(new_event, 'new_event', EventRecord)

        with self._log_storage_lock:
            self._log_sequence = self._log_sequence.append(new_event)


class LogFilePipelineRun(InMemoryPipelineRun):
    def __init__(self, log_dir, *args, **kwargs):
        super(LogFilePipelineRun, self).__init__(*args, **kwargs)
        self._log_dir = check.str_param(log_dir, 'log_dir')
        self._file_prefix = os.path.join(
            self._log_dir, '{}_{}'.format(int(time.time()), self.run_id)
        )
        ensure_dir(log_dir)
        self._write_metadata_to_file()
        self._log_file = '{}.log'.format(self._file_prefix)
        self._log_file_lock = gevent.lock.Semaphore()

    def _write_metadata_to_file(self):
        metadata_file = '{}.json'.format(self._file_prefix)
        with open(metadata_file, 'w', encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        'run_id': self.run_id,
                        'pipeline_name': self.pipeline_name,
                        'config': self.config,
                        'execution_plan': 'TODO',
                    }
                )
            )

    def store_event(self, new_event):
        check.inst_param(new_event, 'new_event', EventRecord)

        super().store_event(new_event)

        with self._log_file_lock:
            # Going to do the less error-prone, simpler, but slower strategy:
            # open, append, close for every log message for now
            with open(self._log_file, 'a', encoding='utf-8') as log_file_handle:
                log_file_handle.write(json.dumps(new_event.to_dict()))
                log_file_handle.write('\n')


def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)


class PipelineRunObservableSubscribe(object):
    def __init__(self, pipeline_run, after_cursor=None):
        self.debouncing_queue = DebouncingLogQueue()
        self.pipeline_run = pipeline_run
        self.observer = None
        self.after_cursor = after_cursor or -1

    def __call__(self, observer):
        self.observer = observer
        events = self.pipeline_run.logs_after(self.after_cursor)
        if events:
            self.observer.on_next(events)
        self.pipeline_run.subscribe(self)

    def handle_new_event(self, new_event):
        self.debouncing_queue.enqueue(new_event)
        gevent.spawn(self._enqueue_flush_logs)

    def _enqueue_flush_logs(self):
        events = self.debouncing_queue.attempt_dequeue()
        if events:
            self.observer.on_next(events)


class LogSequence(pyrsistent.CheckedPVector):
    __type__ = EventRecord


class DebouncingLogQueue(object):
    '''
    A queue that debounces dequeuing operation
    '''

    def __init__(self, timeout_length=1.0, sleep_length=0.1):
        self._log_queue_lock = gevent.lock.Semaphore()
        self._log_sequence = LogSequence()
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
                return LogSequence()
            else:
                self._is_dequeueing_blocked = True

        # wait till we have elapsed timeout_length seconds from first event, while
        # letting other gevent threads do the work (sleep_length is the chosen sleep cycle)
        while (time.time() - self._queue_timeout) < self._timeout_length:
            gevent.sleep(self._sleep_length)

        with self._log_queue_lock:
            events = self._log_sequence
            self._log_sequence = LogSequence()
            self._is_dequeueing_blocked = False
            self._queue_timeout = None
            return events

    def enqueue(self, item):
        with self._log_queue_lock:
            if not self._queue_timeout:
                self._queue_timeout = time.time()
            self._log_sequence = self._log_sequence.append(item)
