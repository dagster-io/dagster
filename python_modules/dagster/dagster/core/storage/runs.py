import glob
import io
import os
import sqlite3
import warnings
from abc import ABCMeta, abstractmethod, abstractproperty
from collections import OrderedDict

import gevent.lock
import six
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

from dagster import check
from dagster.core.events import DagsterEventType
from dagster.core.serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple
from dagster.utils import mkdir_p

from .pipeline_run import PipelineRun, PipelineRunStatus


class RunStorage(six.with_metaclass(ABCMeta)):  # pylint: disable=no-init
    @abstractmethod
    def add_run(self, pipeline_run):
        '''Add a run to storage.

        Args:
            pipeline_run (PipelineRun): The run to add. If this is not a PipelineRun,
        '''

    @abstractmethod
    def handle_run_event(self, run_id, event):
        '''Update run storage in accordance to a pipeline run related DagsterEvent

        Args:
            event (DagsterEvent)

        '''

    @abstractmethod
    def all_runs(self):
        '''Return all the runs present in the storage.

        Returns:
            Iterable[(str, PipelineRun)]: Tuples of run_id, pipeline_run.
        '''

    @abstractmethod
    def all_runs_for_pipeline(self, pipeline_name):
        '''Return all the runs present in the storage for a given pipeline.

        Args:
            pipeline_name (str): The pipeline to index on

        Returns:
            Iterable[(str, PipelineRun)]: Tuples of run_id, pipeline_run.
        '''

    @abstractmethod
    def get_run_by_id(self, run_id):
        '''Get a run by its id.

        Args:
            run_id (str): THe id of the run

        Returns:
            Optional[PipelineRun]
        '''

    @abstractmethod
    def has_run(self, run_id):
        pass

    @abstractmethod
    def wipe(self):
        '''Clears the run storage.'''

    @abstractproperty
    def is_persistent(self):
        '''(bool) Whether the run storage persists after the process that
        created it dies.'''


class InMemoryRunStorage(RunStorage):
    def __init__(self):
        self._runs = OrderedDict()

    def add_run(self, pipeline_run):
        check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
        check.invariant(
            not self._runs.get(pipeline_run.run_id),
            'Can not add same run twice for run_id {run_id}'.format(run_id=pipeline_run.run_id),
        )

        self._runs[pipeline_run.run_id] = pipeline_run
        return pipeline_run

    def handle_run_event(self, run_id, event):
        run = self._runs[run_id]

        if event.event_type == DagsterEventType.PIPELINE_START:
            self._runs[run_id] = run.run_with_status(PipelineRunStatus.STARTED)
        elif event.event_type == DagsterEventType.PIPELINE_SUCCESS:
            self._runs[run_id] = run.run_with_status(PipelineRunStatus.SUCCESS)
        elif event.event_type == DagsterEventType.PIPELINE_FAILURE:
            self._runs[run_id] = self._runs[run_id].run_with_status(PipelineRunStatus.FAILURE)

    @property
    def all_runs(self):
        return self._runs.values()

    def all_runs_for_pipeline(self, pipeline_name):
        return [r for r in self.all_runs if r.pipeline_name == pipeline_name]

    def get_run_by_id(self, run_id):
        return self._runs.get(run_id)

    def has_run(self, run_id):
        return run_id in self._runs

    @property
    def is_persistent(self):
        return False

    def wipe(self):
        self._runs = OrderedDict()


class FilesystemRunStorage(RunStorage):
    def __init__(self, base_dir, watch_external_runs=True):
        self._base_dir = check.opt_str_param(base_dir, 'base_dir')
        mkdir_p(self._base_dir)

        self._known_runs = OrderedDict()
        self._lock = gevent.lock.Semaphore()

        self._load_historic_runs()

        if watch_external_runs:
            observer = Observer()
            observer.schedule(ExternalRunsWatchdog(self, self._lock), self._base_dir)
            observer.start()

    def filepath_for_run_id(self, run_id):
        return os.path.join(self._base_dir, '{run_id}.json'.format(run_id=run_id))

    def add_run(self, pipeline_run):
        check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
        check.invariant(
            not self._known_runs.get(pipeline_run.run_id),
            'Can not add run for known run_id {run_id}'.format(run_id=pipeline_run.run_id),
        )

        # mark pipeline known before writing to prevent any race issues with the watcher
        self._known_runs[pipeline_run.run_id] = self._write_metadata_to_file(pipeline_run)
        return pipeline_run

    def add_external_run(self, pipeline_run, path):
        self._known_runs[pipeline_run.run_id] = path
        return pipeline_run

    @property
    def runs(self):
        return {run_id: self.get_run_by_id(run_id) for run_id in self._known_runs}

    @property
    def all_runs(self):
        return [self.get_run_by_id(run_id) for run_id in self._known_runs]

    def has_run(self, run_id):
        return run_id in self._known_runs

    def _load_historic_runs(self):
        for filename in glob.glob(os.path.join(self._base_dir, '*.json')):
            with open(filename, 'r') as fd:
                try:
                    pipeline_run = deserialize_json_to_dagster_namedtuple(fd.read())
                    self.add_run(pipeline_run)
                except Exception as ex:  # pylint: disable=broad-except
                    print(
                        'Could not load pipeline run from {filename}, continuing.\n  Original '
                        'exception: {ex}: {msg}'.format(
                            filename=filename, ex=type(ex).__name__, msg=ex
                        )
                    )
                    continue

    def wipe(self):
        for filename in glob.glob(os.path.join(self._base_dir, '*.json')):
            os.unlink(filename)
        self._known_runs = OrderedDict()

    def all_runs_for_pipeline(self, pipeline_name):
        return [r for r in self.all_runs if r.pipeline_name == pipeline_name]

    def get_run_by_id(self, run_id):
        path = self._known_runs[run_id]
        with open(path, 'r') as fd:
            return deserialize_json_to_dagster_namedtuple(fd.read())

    def handle_run_event(self, run_id, event):
        run = self.get_run_by_id(run_id)

        if event.event_type == DagsterEventType.PIPELINE_START:
            updated_run = run.run_with_status(PipelineRunStatus.STARTED)
        elif event.event_type == DagsterEventType.PIPELINE_SUCCESS:
            updated_run = run.run_with_status(PipelineRunStatus.SUCCESS)
        elif event.event_type == DagsterEventType.PIPELINE_FAILURE:
            updated_run = run.run_with_status(PipelineRunStatus.FAILURE)
        else:
            return

        self._write_metadata_to_file(updated_run)

    @property
    def is_persistent(self):
        return True

    def _write_metadata_to_file(self, pipeline_run):
        metadata_filepath = self.filepath_for_run_id(pipeline_run.run_id)

        with self._lock:
            with io.open(metadata_filepath, 'w', encoding='utf-8') as f:
                f.write(six.text_type(serialize_dagster_namedtuple(pipeline_run)))

            return metadata_filepath


class ExternalRunsWatchdog(PatternMatchingEventHandler):
    def __init__(self, run_storage, lock, **kwargs):
        check.inst_param(run_storage, 'run_storage', FilesystemRunStorage)
        self._run_storage = run_storage
        self._lock = lock
        super(ExternalRunsWatchdog, self).__init__(patterns=['*.json'], **kwargs)

    def on_created(self, event):
        run_id, _extension = os.path.basename(event.src_path).split('.')
        # if we already know about the run, we kicked it off
        with self._lock:
            if self._run_storage.has_run(run_id):
                return

            with open(event.src_path, 'r') as fd:
                try:
                    pipeline_run = deserialize_json_to_dagster_namedtuple(fd.read())
                    self._run_storage.add_external_run(pipeline_run, event.src_path)
                except Exception as ex:  # pylint: disable=broad-except
                    warnings.warn(
                        'Error trying to load .json metadata file in filesystem run '
                        'storage at path "{path}": {ex}: {msg}'.format(
                            path=event.src_path, ex=type(ex).__name__, msg=ex
                        )
                    )
                    return


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
        return pipeline_run

    @property
    def all_runs(self):
        raw_runs = self.conn.cursor().execute('SELECT run_id, pipeline_name FROM runs').fetchall()
        return list(map(self._from_sql_row, raw_runs))

    def _from_sql_row(self, row):
        return PipelineRun.create_empty_run(run_id=row[0], pipeline_name=row[1])

    def handle_run_event(self, run_id, event):
        raise NotImplementedError()

    def all_runs_for_pipeline(self, pipeline_name):
        raw_runs = (
            self.conn.cursor()
            .execute(
                'SELECT run_id, pipeline_name FROM runs WHERE pipeline_name=?', (pipeline_name,)
            )
            .fetchall()
        )
        return list(map(self._from_sql_row, raw_runs))

    def get_run_by_id(self, run_id):
        sql = 'SELECT run_id, pipeline_name FROM runs WHERE run_id = ?'
        return self._from_sql_row(self.conn.cursor().execute(sql, (run_id,)).fetchone())

    def has_run(self, run_id):
        sql = 'SELECT run_id FROM runs WHERE run_id = ?'
        return bool(self.conn.cursor().execute(sql, (run_id,)).fetchone())

    def wipe(self):
        self.conn.execute('DELETE FROM runs')

    @property
    def is_persistent(self):
        return True

    def get_logs_for_run(self, run_id, cursor=0):
        raise NotImplementedError()
