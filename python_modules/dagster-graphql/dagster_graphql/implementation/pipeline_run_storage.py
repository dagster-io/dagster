import atexit
import os
import time

from collections import OrderedDict
from enum import Enum

import gevent
import gevent.lock
import pyrsistent

from rx import Observable

from dagster import check, seven
from dagster.core.events.logging import EventRecord
from dagster.core.events import DagsterEventType
from dagster.core.execution.api import ExecutionSelector
from dagster.core.execution.execution_context import ReexecutionConfig
from dagster.core.execution_plan.plan import ExecutionPlan


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
    def __init__(
        self, run_id, selector, env_config, execution_plan, reexecution_config, step_keys_to_execute
    ):
        self.__subscribers = []

        self._status = PipelineRunStatus.NOT_STARTED
        self._run_id = check.str_param(run_id, 'run_id')
        self._selector = check.inst_param(selector, 'selector', ExecutionSelector)
        self._env_config = check.opt_dict_param(env_config, 'environment_config', key_type=str)
        self._execution_plan = check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
        self._reexecution_config = check.opt_inst_param(
            reexecution_config, 'reexecution_config', ReexecutionConfig
        )
        check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)
        self._step_keys_to_execute = step_keys_to_execute

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
    def execution_plan(self):
        return self._execution_plan

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
                seven.json.dumps(
                    {
                        'run_id': self.run_id,
                        'pipeline_name': self.selector.name,
                        'pipeline_solid_subset': self.selector.solid_subset,
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
                log_file_handle.write(seven.json.dumps(new_event.to_dict()))
                log_file_handle.write('\n')


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
