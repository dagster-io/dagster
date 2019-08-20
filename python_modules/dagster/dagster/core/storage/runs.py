import abc
import glob
import io
import json
import os
import pickle
import shutil
import sqlite3
import weakref
from collections import defaultdict, OrderedDict
from enum import Enum

import gevent.lock
import pyrsistent
import six
from rx import Observable

from dagster import check, seven
from dagster.core.events import DagsterEventType
from dagster.core.events.log import EventRecord
from dagster.utils import mkdir_p

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
    def create_run(self, **kwargs):
        '''Create a new run in storage.

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

    @abc.abstractmethod
    def get_logs_for_run(self, run_id, cursor=-1):
        pass


class InMemoryEventHandler(object):
    def __init__(self, pipeline_run, run_storage):
        self.pipeline_run = pipeline_run
        self.run_storage = run_storage

    def handle_new_event(self, event):
        check.inst_param(event, 'new_event', EventRecord)

        with self.run_storage.log_storage_lock[self.pipeline_run.run_id]:
            self.run_storage.log_storage[self.pipeline_run.run_id] = self.run_storage.log_storage[
                self.pipeline_run.run_id
            ].append(event)


class InMemoryRunStorage(RunStorage):
    def __init__(self):
        self._runs = OrderedDict()
        self.log_storage = defaultdict(LogSequence)
        self.log_storage_lock = defaultdict(gevent.lock.Semaphore)

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

    def create_run(self, **kwargs):
        kwargs['run_storage'] = self
        pipeline_run = PipelineRun(**kwargs)
        self.add_run(pipeline_run)
        pipeline_run.subscribe(InMemoryEventHandler(pipeline_run, self))
        return pipeline_run

    def get_logs_for_run(self, run_id, cursor=-1):
        cursor = int(cursor) + 1
        with self.log_storage_lock[run_id]:
            return self.log_storage[run_id][cursor:]


class FilesystemEventHandler(object):
    def __init__(self, pipeline_run, run_storage):
        self.pipeline_run = pipeline_run
        self.run_storage = run_storage

    def handle_new_event(self, event):
        check.inst_param(event, 'new_event', EventRecord)
        with self.run_storage.log_file_lock[self.pipeline_run.run_id]:
            # Going to do the less error-prone, simpler, but slower strategy:
            # open, append, close for every log message for now.
            # Open the file for binary content and create if it doesn't exist.
            with open(
                self.run_storage.log_filepath_for_run_id(self.pipeline_run.run_id), 'ab'
            ) as log_file_handle:
                log_file_handle.seek(0, os.SEEK_END)
                pickle.dump(event, log_file_handle)


class FilesystemRunStorage(RunStorage):
    def __init__(self, log_dir=None):
        self._log_dir = check.opt_str_param(log_dir, 'log_dir', base_runs_directory())
        mkdir_p(self._log_dir)

        self._runs = OrderedDict()

        self._load_runs()

        self.log_file_cursors = defaultdict(lambda: (0, 0))
        # Swap these out to use lockfiles
        self.log_file_lock = defaultdict(gevent.lock.Semaphore)
        self._metadata_file_lock = defaultdict(gevent.lock.Semaphore)

    def log_filepath_for_run_id(self, run_id):
        return os.path.join(self._log_dir, '{run_id}.log'.format(run_id=run_id))

    def _metadata_filepath_for_run_id(self, run_id):
        return os.path.join(self._log_dir, '{run_id}.json'.format(run_id=run_id))

    def add_run(self, pipeline_run):
        check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
        self._runs[pipeline_run.run_id] = pipeline_run

    @property
    def all_runs(self):
        return self._runs.values()

    def _load_run(self, json_data):
        from dagster.core.execution.api import ExecutionSelector

        selector = ExecutionSelector(
            name=json_data['pipeline_name'], solid_subset=json_data.get('pipeline_solid_subset')
        )
        self.create_run(
            pipeline_name=json_data['pipeline_name'],
            run_id=json_data['run_id'],
            selector=selector,
            env_config=json_data['config'],
            mode=json_data['mode'],
        )

    def _load_runs(self):
        for filename in glob.glob(os.path.join(self._log_dir, '*.json')):
            with open(filename, 'r') as fd:
                try:
                    self._load_run(json.load(fd))
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

    def all_runs_for_pipeline(self, pipeline_name):
        return [r for r in self.all_runs if r.pipeline_name == pipeline_name]

    def get_run_by_id(self, run_id):
        return self._runs.get(run_id)

    def __getitem__(self, run_id):
        return self.get_run_by_id(run_id)

    def __contains__(self, run_id):
        return run_id in self._runs

    def create_run(self, **kwargs):
        kwargs['run_storage'] = self
        pipeline_run = PipelineRun(**kwargs)
        self.add_run(pipeline_run)
        self._write_metadata_to_file(pipeline_run)
        pipeline_run.subscribe(FilesystemEventHandler(pipeline_run, self))
        return pipeline_run

    @property
    def is_persistent(self):
        return True

    def get_logs_for_run(self, run_id, cursor=0):
        events = []
        with self.log_file_lock[run_id]:
            with open(self.log_filepath_for_run_id(run_id), 'rb') as fd:
                # There might be a path to make this more performant, at the expense of interop,
                # by using a modified file format: https://stackoverflow.com/a/8936927/324449
                # Alternatively, we could use .jsonl and linecache instead of pickle
                if cursor == self.log_file_cursors[run_id][0]:
                    fd.seek(self.log_file_cursors[run_id][1])
                else:
                    i = 0
                    while i < cursor:
                        pickle.load(fd)
                        i = fd.tell()
                try:
                    while True:
                        events.append(pickle.load(fd))
                except EOFError:
                    pass
        return events

    def _write_metadata_to_file(self, pipeline_run):
        metadata_filepath = self._metadata_filepath_for_run_id(pipeline_run.run_id)

        with io.open(metadata_filepath, 'w', encoding='utf-8') as f:
            json_str = seven.json.dumps(
                {
                    'run_id': pipeline_run.run_id,
                    'pipeline_name': pipeline_run.pipeline_name,
                    'pipeline_solid_subset': pipeline_run.selector.solid_subset,
                    'config': pipeline_run.config,
                    'mode': pipeline_run.mode,
                    'log_file': self.log_filepath_for_run_id(pipeline_run.run_id),
                }
            )
            f.write(six.text_type(json_str))


CREATE_RUNS_TABLE_STATEMENT = '''
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
        conn.execute(CREATE_RUNS_TABLE_STATEMENT)
        conn.commit()
        return SqliteRunStorage(conn)

    def __init__(self, conn):
        self.conn = conn

    def add_run(self, pipeline_run):
        self.conn.execute(INSERT_RUN_STATEMENT, (pipeline_run.run_id, pipeline_run.pipeline_name))

    def create_run(self, **kwargs):
        kwargs['run_storage'] = self
        run = PipelineRun(**kwargs)
        self.add_run(run)
        return run

    @property
    def all_runs(self):
        raw_runs = self.conn.cursor().execute('SELECT run_id, pipeline_name FROM runs').fetchall()
        return list(map(lambda x: PipelineRun(run_id=x[0], pipeline_name=x[1]), raw_runs))

    def all_runs_for_pipeline(self, pipeline_name):
        raw_runs = (
            self.conn.cursor()
            .execute(
                'SELECT run_id, pipeline_name FROM runs WHERE pipeline_name=?', (pipeline_name,)
            )
            .fetchall()
        )
        return list(map(lambda x: PipelineRun(run_id=x[0], pipeline_name=x[1]), raw_runs))

    def get_run_by_id(self, run_id):
        sql = 'SELECT run_id, pipeline_name FROM runs WHERE run_id = ?'

        return (lambda x: PipelineRun(run_id=x[0], pipeline_name=x[1]))(
            self.conn.cursor().execute(sql, (run_id,)).fetchone()
        )

    def wipe(self):
        self.conn.execute('DELETE FROM runs')

    @property
    def is_persistent(self):
        return True

    def get_logs_for_run(self, run_id, cursor=0):
        raise NotImplementedError()


class PipelineRun(object):
    def __init__(
        self,
        run_storage=None,
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

        run_storage = check.opt_inst_param(run_storage, 'run_storage', RunStorage)
        if run_storage:
            self._run_storage = weakref.proxy(run_storage)
        else:
            self._run_storage = None

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
        return self._run_storage.get_logs_for_run(self.run_id, cursor=cursor)

    def all_logs(self):
        return self._run_storage.get_logs_for_run(self.run_id)

    @property
    def selector(self):
        return self._selector

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

        for subscriber in self.__subscribers:
            subscriber.handle_new_event(new_event)

    def subscribe(self, subscriber):
        self.__subscribers.append(subscriber)

    def observable_after_cursor(self, observable_cls=None, cursor=None):
        check.type_param(observable_cls, 'observable_cls')
        return Observable.create(observable_cls(self, cursor))  # pylint: disable=E1101


class LogSequence(pyrsistent.CheckedPVector):
    __type__ = EventRecord
