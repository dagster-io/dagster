import atexit
import io
import json
import os
import pickle
import time
from collections import OrderedDict
from enum import Enum

import gevent
import gevent.lock
import pyrsistent
import six
from rx import Observable

from dagster import check, seven
from dagster.core.events import DagsterEventType
from dagster.core.events.log import EventRecord
from dagster.core.execution.api import ExecutionSelector
from dagster.core.execution.config import ReexecutionConfig


class PipelineRunStatus(Enum):
    NOT_STARTED = 'NOT_STARTED'
    STARTED = 'STARTED'
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'


class PipelineRunStorage(object):
    def __init__(self, log_dir=None):
        self._runs = OrderedDict()
        self._log_dir = log_dir
        if self._log_dir:
            self._load_runs()

    def _load_runs(self):
        for file in os.listdir(self._log_dir):
            if not file.endswith('.json'):
                continue
            with open(os.path.join(self._log_dir, file)) as data:
                try:
                    self.add_run(InMemoryPipelineRun.from_json(json.load(data)))
                except Exception as ex:  # pylint: disable=broad-except
                    print(
                        'Could not parse dagit run from {file_name} in {dir_name}. {ex}: {msg}'.format(
                            file_name=file, dir_name=self._log_dir, ex=type(ex).__name__, msg=ex
                        )
                    )
                    continue

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
        if self._log_dir:
            return LogFilePipelineRun(self._log_dir, *args, **kwargs)
        else:
            return InMemoryPipelineRun(*args, **kwargs)


class PipelineRun(object):
    def __init__(
        self, run_id, selector, env_config, mode, reexecution_config=None, step_keys_to_execute=None
    ):
        self.__subscribers = []

        self._status = PipelineRunStatus.NOT_STARTED
        self._run_id = check.str_param(run_id, 'run_id')
        self._selector = check.inst_param(selector, 'selector', ExecutionSelector)
        self._env_config = check.opt_dict_param(env_config, 'environment_config', key_type=str)
        self._mode = check.str_param(mode, 'mode')
        self._reexecution_config = check.opt_inst_param(
            reexecution_config, 'reexecution_config', ReexecutionConfig
        )
        check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)
        self._step_keys_to_execute = step_keys_to_execute

    @property
    def mode(self):
        return self._mode

    @property
    def run_id(self):
        return self._run_id

    @property
    def status(self):
        return self._status

    @property
    def pipeline_name(self):
        return self._selector.name

    @property
    def selector(self):
        return self._selector

    @property
    def config(self):
        return self._env_config

    @property
    def reexecution_config(self):
        return self._reexecution_config

    @property
    def step_keys_to_execute(self):
        return self._step_keys_to_execute

    def logs_after(self, cursor):
        raise NotImplementedError()

    def all_logs(self):
        raise NotImplementedError()

    def store_event(self, new_event):
        raise NotImplementedError()

    def handle_new_event(self, new_event):
        check.inst_param(new_event, 'new_event', EventRecord)

        if new_event.is_dagster_event:
            event = new_event.dagster_event
            if event.event_type == DagsterEventType.PIPELINE_START:
                self._status = PipelineRunStatus.STARTED
            elif event.event_type == DagsterEventType.PIPELINE_SUCCESS:
                self._status = PipelineRunStatus.SUCCESS
            elif event.event_type == DagsterEventType.PIPELINE_FAILURE:
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

    def store_events(self, new_events):
        check.list_param(new_events, 'new_events', of_type=EventRecord)

        with self._log_storage_lock:
            self._log_sequence = self._log_sequence.extend(new_events)

    @staticmethod
    def from_json(data):
        selector = ExecutionSelector(
            name=data['pipeline_name'], solid_subset=data.get('pipeline_solid_subset')
        )
        run = InMemoryPipelineRun(
            run_id=data['run_id'], selector=selector, env_config=data['config'], mode=data['mode']
        )
        events = []
        with open(data['log_file'], 'rb') as logs:
            while True:
                try:
                    event_record = pickle.load(logs)
                    check.invariant(
                        isinstance(event_record, EventRecord), 'log file entry not EventRecord'
                    )
                    events.append(event_record)
                except EOFError:
                    break

        run.store_events(events)
        return run


class LogFilePipelineRun(InMemoryPipelineRun):
    def __init__(self, log_dir, *args, **kwargs):
        super(LogFilePipelineRun, self).__init__(*args, **kwargs)
        self._log_dir = check.str_param(log_dir, 'log_dir')
        self._file_prefix = os.path.join(
            self._log_dir, '{}_{}'.format(int(time.time()), self.run_id)
        )
        ensure_dir(log_dir)
        self._log_file = '{}.log'.format(self._file_prefix)
        self._log_file_lock = gevent.lock.Semaphore()
        self._write_metadata_to_file()

    def _write_metadata_to_file(self):
        metadata_file = '{}.json'.format(self._file_prefix)
        with io.open(metadata_file, 'w', encoding='utf-8') as f:
            json_str = seven.json.dumps(
                {
                    'run_id': self.run_id,
                    'pipeline_name': self.selector.name,
                    'pipeline_solid_subset': self.selector.solid_subset,
                    'config': self.config,
                    'mode': self.mode,
                    'log_file': self._log_file,
                }
            )
            f.write(six.text_type(json_str))

    def store_event(self, new_event):
        check.inst_param(new_event, 'new_event', EventRecord)

        super(LogFilePipelineRun, self).store_event(new_event)

        with self._log_file_lock:
            # Going to do the less error-prone, simpler, but slower strategy:
            # open, append, close for every log message for now.
            # Open the file for binary content and create if it doesn't exist.
            with open(self._log_file, 'ab') as log_file_handle:
                log_file_handle.seek(0, os.SEEK_END)
                pickle.dump(new_event, log_file_handle)


def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)


class PipelineRunObservableSubscribe(object):
    def __init__(self, pipeline_run, after_cursor=None):
        self.log_sequence = LogSequence()
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
            self.log_sequence = self.log_sequence.append(new_event)

            if self.flush_after is None:
                self.observer.on_next(self.log_sequence)
                self.log_sequence = LogSequence()
                return

            if not self.flush_scheduled:
                self.flush_scheduled = True
                gevent.spawn(self._flush_logs_after_delay)

    def _flush_logs_after_delay(self):
        gevent.sleep(self.flush_after)
        with self.lock:
            self.observer.on_next(self.log_sequence)
            self.log_sequence = LogSequence()
            self.flush_scheduled = False

    def _cleanup(self):
        # Make incoming logs flush immediately to ensure we communciate failures
        # to client on unexpected exit
        self.flush_after = None


class LogSequence(pyrsistent.CheckedPVector):
    __type__ = EventRecord
