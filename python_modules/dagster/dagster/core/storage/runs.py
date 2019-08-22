import abc
import glob
import io
import json
import os
import sqlite3
from collections import defaultdict, OrderedDict

import gevent.lock
import six

from dagster import check, seven
from dagster.utils import mkdir_p

from .config import base_runs_directory
from .event_log import EventLogStorage, InMemoryEventLogStorage, FilesystemEventLogStorage
from .pipeline_run import PipelineRun


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


class InMemoryRunStorage(RunStorage):
    def __init__(self, event_log_storage=None):
        self.event_log_storage = check.opt_inst_param(
            event_log_storage,
            'event_log_storage',
            EventLogStorage,
            default=InMemoryEventLogStorage(),
        )
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

    def create_run(self, **kwargs):
        kwargs['run_storage'] = self
        pipeline_run = PipelineRun(**kwargs)
        self.add_run(pipeline_run)
        pipeline_run.subscribe(self.event_log_storage.event_handler(pipeline_run))
        return pipeline_run


class FilesystemRunStorage(RunStorage):
    def __init__(self, event_log_storage=None, base_dir=None):
        self._base_dir = check.opt_str_param(base_dir, 'base_dir', base_runs_directory())
        mkdir_p(self._base_dir)

        self._runs = OrderedDict()

        self._load_runs()

        self._file_lock = defaultdict(gevent.lock.Semaphore)

        self.event_log_storage = check.opt_inst_param(
            event_log_storage,
            'event_log_storage',
            EventLogStorage,
            default=FilesystemEventLogStorage(base_dir=self._base_dir),
        )

    def filepath_for_run_id(self, run_id):
        return os.path.join(self._base_dir, '{run_id}.json'.format(run_id=run_id))

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
        for filename in glob.glob(os.path.join(self._base_dir, '*.json')):
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
        for filename in glob.glob(os.path.join(self._base_dir, '*.json')):
            os.unlink(filename)
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
        pipeline_run.subscribe(self.event_log_storage.event_handler(pipeline_run))
        return pipeline_run

    @property
    def is_persistent(self):
        return True

    def _write_metadata_to_file(self, pipeline_run):
        metadata_filepath = self.filepath_for_run_id(pipeline_run.run_id)

        with io.open(metadata_filepath, 'w', encoding='utf-8') as f:
            metadata = {
                'run_id': pipeline_run.run_id,
                'pipeline_name': pipeline_run.pipeline_name,
                'pipeline_solid_subset': pipeline_run.selector.solid_subset,
                'config': pipeline_run.config,
                'mode': pipeline_run.mode,
            }
            if isinstance(self.event_log_storage, FilesystemEventLogStorage):
                metadata['log_file'] = self.event_log_storage.filepath_for_run_id(
                    pipeline_run.run_id
                )

            json_str = seven.json.dumps(metadata)
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
