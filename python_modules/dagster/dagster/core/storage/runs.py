import abc
import glob
import io
import json
import os
import pickle
import shutil
import sqlite3
import time
from collections import OrderedDict
from enum import Enum

import gevent.lock
import pyrsistent
import six
from rx import Observable

from dagster import check, seven
from dagster.core.events import DagsterEventType
from dagster.core.events.log import EventRecord
from dagster.utils import ensure_dir, mkdir_p

from .config import base_runs_directory


class PipelineRunStatus(Enum):
    NOT_STARTED = 'NOT_STARTED'
    STARTED = 'STARTED'
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'


class RunStorage(six.with_metaclass(abc.ABCMeta)):  # pylint: disable=no-init
    @abc.abstractmethod
    def add_run(self, pipeline_run):
        '''Add a run to storage.

        Args:
            pipeline_run (PipelineRun): The run to add. If this is not a PipelineRun,
        '''

    @abc.abstractmethod
    def create_run(self, *args, **kwargs):
        '''Create a new run in storage.

        Takes the *args and **kwargs of self.pipeline_run_class.

        Returns:
            (PipelineRun) The new pipeline run.
        '''

    @abc.abstractmethod
    def all_runs(self):
        '''Return all the runs present in the storage.

        Returns:
            Iterable[(str, PipelineRun)]: Tuples of run_id, pipeline_run.
        '''

    @abc.abstractmethod
    def all_runs_for_pipeline(self, pipeline_name):
        '''Return all the runs present in the storage for a given pipeline.

        Args:
            pipeline_name (str): The pipeline to index on

        Returns:
            Iterable[(str, PipelineRun)]: Tuples of run_id, pipeline_run.
        '''

    @abc.abstractmethod
    def get_run_by_id(self, run_id):
        '''Get a run by its id.

        Args:
            run_id (str): THe id of the run

        Returns:
            Optional[PipelineRun]
        '''

    @abc.abstractmethod
    def wipe(self):
        '''Clears the run storage.'''

    @property
    @abc.abstractmethod
    def is_persistent(self):
        '''(bool) Whether the run storage persists after the process that
        created it dies.'''

    @property
    @classmethod
    @abc.abstractmethod
    def pipeline_run_class(cls):
        '''(Type[PipelineRun]) The subclass of PipelineRun appropriate to this storage class.'''


class InMemoryRunStorage(RunStorage):
    def __init__(self):
        self._runs = OrderedDict()

    def add_run(self, pipeline_run):
        check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
        self._runs[pipeline_run.run_id] = pipeline_run

    @property
    def all_runs(self):
        return self._runs.values()

    def all_runs_for_pipeline(self, pipeline_name):
        return [r for r in self.all_runs if r.pipeline_name == pipeline_name]

    def get_run_by_id(self, run_id):
        return self._runs.get(run_id)

    def __getitem__(self, run_id):
        return self.get_run_by_id(run_id)

    def __contains__(self, run_id):
        return run_id in self._runs

    @property
    def is_persistent(self):
        return False

    def wipe(self):
        self._runs = OrderedDict()

    @property
    def pipeline_run_class(self):
        return InMemoryPipelineRun

    def create_run(self, *args, **kwargs):
        pipeline_run = self.pipeline_run_class(*args, **kwargs)
        self.add_run(pipeline_run)
        return pipeline_run


class FilesystemRunStorage(InMemoryRunStorage):
    def __init__(self, log_dir=None):
        self._log_dir = check.opt_str_param(log_dir, 'log_dir', base_runs_directory())
        mkdir_p(self._log_dir)

        super(FilesystemRunStorage, self).__init__()

        self._load_runs()

    def _load_runs(self):
        for filename in glob.glob(os.path.join(self._log_dir, '*.json')):
            with open(filename, 'r') as fd:
                try:
                    self.add_run(InMemoryPipelineRun.from_json(json.load(fd), self))
                except Exception as ex:  # pylint: disable=broad-except
                    print(
                        'Could not parse pipeline run from {filename}, continuing. Original '
                        'exception: {ex}: {msg}'.format(
                            filename=filename, ex=type(ex).__name__, msg=ex
                        )
                    )
                    continue

    def wipe(self):
        shutil.rmtree(os.path.join(self._log_dir, ''))
        self._runs = OrderedDict([])

    @property
    def pipeline_run_class(self):
        return LogFilePipelineRun

    def create_run(self, *args, **kwargs):
        pipeline_run = self.pipeline_run_class(self._log_dir, *args, **kwargs)
        self.add_run(pipeline_run)
        return pipeline_run

    @property
    def is_persistent(self):
        return True


class PipelineRun(object):
    def __init__(
        self,
        pipeline_name=None,
        run_id=None,
        env_config=None,
        mode=None,
        selector=None,
        reexecution_config=None,
        step_keys_to_execute=None,
    ):
        from dagster.core.execution.api import ExecutionSelector
        from dagster.core.execution.config import ReexecutionConfig

        self._pipeline_name = check.str_param(pipeline_name, 'pipeline_name')
        self._run_id = check.str_param(run_id, 'run_id')
        self._env_config = check.opt_dict_param(env_config, 'environment_config', key_type=str)
        self._mode = check.opt_str_param(mode, 'mode')
        self._selector = check.opt_inst_param(
            selector,
            'selector',
            ExecutionSelector,
            default=ExecutionSelector(name=self.pipeline_name),
        )
        self._reexecution_config = check.opt_inst_param(
            reexecution_config, 'reexecution_config', ReexecutionConfig
        )
        if step_keys_to_execute is not None:
            self._step_keys_to_execute = check.list_param(
                step_keys_to_execute, 'step_keys_to_execute', of_type=str
            )
        else:
            self._step_keys_to_execute = None

        self.__subscribers = []

        self._status = PipelineRunStatus.NOT_STARTED

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
    def is_persistent(self):
        return False

    @property
    def pipeline_name(self):
        return self._pipeline_name

    @property
    def config(self):
        return self._env_config

    def logs_after(self, cursor):
        raise NotImplementedError()

    def all_logs(self):
        raise NotImplementedError()

    @property
    def selector(self):
        return self._selector

    def store_event(self, new_event):
        pass

    @property
    def reexecution_config(self):
        return self._reexecution_config

    @property
    def step_keys_to_execute(self):
        return self._step_keys_to_execute

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

    def observable_after_cursor(self, observable_cls=None, cursor=None):
        check.type_param(observable_cls, 'observable_cls')
        return Observable.create(observable_cls(self, cursor))  # pylint: disable=E1101


CREATE_RUNS_TABLE = '''
    CREATE TABLE IF NOT EXISTS runs (
        run_id varchar(255) NOT NULL,
        pipeline_name varchar(1023) NOT NULL
    )
'''

INSERT_RUN_STATEMENT = '''
    INSERT INTO runs (run_id, pipeline_name) VALUES (?, ?)
'''


class SqliteRunStorage(RunStorage):
    @staticmethod
    def mem():
        conn = sqlite3.connect(':memory:')
        conn.execute(CREATE_RUNS_TABLE)
        conn.commit()
        return SqliteRunStorage(conn)

    def __init__(self, conn):
        self.conn = conn

    def add_run(self, pipeline_run):
        self.conn.execute(INSERT_RUN_STATEMENT, (pipeline_run.run_id, pipeline_run.pipeline_name))

    def create_run(self, *args, **kwargs):
        run = InMemoryPipelineRun(*args, **kwargs)
        self.add_run(run)
        return run

    @property
    def all_runs(self):
        raw_runs = self.conn.cursor().execute('SELECT run_id, pipeline_name FROM runs').fetchall()
        return list(map(lambda x: InMemoryPipelineRun(run_id=x[0], pipeline_name=x[1]), raw_runs))

    def all_runs_for_pipeline(self, pipeline_name):
        raw_runs = (
            self.conn.cursor()
            .execute(
                'SELECT run_id, pipeline_name FROM runs WHERE pipeline_name=?', (pipeline_name,)
            )
            .fetchall()
        )
        return list(map(lambda x: InMemoryPipelineRun(run_id=x[0], pipeline_name=x[1]), raw_runs))

    def get_run_by_id(self, run_id):
        sql = 'SELECT run_id, pipeline_name FROM runs WHERE run_id = ?'

        return (lambda x: InMemoryPipelineRun(run_id=x[0], pipeline_name=x[1]))(
            self.conn.cursor().execute(sql, (run_id,)).fetchone()
        )

    def wipe(self):
        self.conn.execute('DELETE FROM runs')

    @property
    def is_persistent(self):
        return True

    @property
    def pipeline_run_class(self):
        return InMemoryPipelineRun


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
    def from_json(data, run_storage):
        from dagster.core.execution.api import ExecutionSelector

        check.opt_inst_param(run_storage, 'run_storage', RunStorage)
        selector = ExecutionSelector(
            name=data['pipeline_name'], solid_subset=data.get('pipeline_solid_subset')
        )
        run = InMemoryPipelineRun(
            pipeline_name=data['pipeline_name'],
            run_id=data['run_id'],
            selector=selector,
            env_config=data['config'],
            mode=data['mode'],
        )
        events = []
        try:
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
        except seven.FileNotFoundError:
            pass

        run.store_events(events)

        if run_storage:
            run_storage.add_run(run)
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
                    'pipeline_name': self.pipeline_name,
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


class LogSequence(pyrsistent.CheckedPVector):
    __type__ = EventRecord
