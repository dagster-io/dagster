import os
import sqlite3
from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from contextlib import contextmanager
from datetime import datetime

import six

from dagster import check
from dagster.core.definitions.environment_configs import SystemNamedDict
from dagster.core.events import DagsterEvent, DagsterEventType
from dagster.core.serdes import (
    ConfigurableClass,
    deserialize_json_to_dagster_namedtuple,
    serialize_dagster_namedtuple,
)
from dagster.core.types import Field, String
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
    def all_runs_for_tag(self, key, value):
        '''Return all the runs present in the storage that have a tag with key, value

        Args:
            key (str): The key to index on
            value (str): The value to match

        Returns:
            Iterable[(str, PipelineRun)]: Tuples of run_id, pipeline_run.
        '''

    @abstractmethod
    def get_run_by_id(self, run_id):
        '''Get a run by its id.

        Args:
            run_id (str): The id of the run

        Returns:
            Optional[PipelineRun]
        '''

    @abstractmethod
    def has_run(self, run_id):
        pass

    @abstractmethod
    def wipe(self):
        '''Clears the run storage.'''


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

    def all_runs(self):
        return self._runs.values()

    def all_runs_for_pipeline(self, pipeline_name):
        return [r for r in self.all_runs() if r.pipeline_name == pipeline_name]

    def get_run_by_id(self, run_id):
        return self._runs.get(run_id)

    def all_runs_for_tag(self, key, value):
        return [r for r in self.all_runs() if r.tags.get(key) == value]

    def has_run(self, run_id):
        return run_id in self._runs

    def wipe(self):
        self._runs = OrderedDict()


CREATE_RUNS_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS runs (
    run_id VARCHAR(255) NOT NULL,
    pipeline_name VARCHAR NOT NULL,
    status VARCHAR(63) NOT NULL,
    run_body VARCHAR NOT NULL,
    create_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
'''
INSERT_RUN_SQL = 'INSERT INTO runs (run_id, pipeline_name, status, run_body) VALUES (?, ?, ?, ?)'
DELETE_RUNS_SQL = 'DELETE FROM runs'
CREATE_RUN_TAGS_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS run_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id VARCHAR(255) NOT NULL,
    key VARCHAR NOT NULL,
    value VARCHAR NOT NULL
)
'''
INSERT_RUN_TAGS_SQL = 'INSERT INTO run_tags (run_id, key, value) VALUES (?, ?, ?)'
DELETE_RUN_TAGS_SQL = 'DELETE FROM run_tags'


class SqliteRunStorage(RunStorage, ConfigurableClass):
    def __init__(self, conn_string, inst_data=None):
        self.conn_string = conn_string
        super(SqliteRunStorage, self).__init__(inst_data=inst_data)

    @classmethod
    def config_type(cls):
        return SystemNamedDict('SqliteRunStorageConfig', {'base_dir': Field(String)})

    @staticmethod
    def from_config_value(config_value, **kwargs):
        return SqliteRunStorage.from_local(**dict(config_value, **kwargs))

    @staticmethod
    def from_local(base_dir, inst_data=None):
        mkdir_p(base_dir)
        conn_string = os.path.join(base_dir, 'runs.db')
        try:
            with sqlite3.connect(conn_string) as conn:
                conn.cursor().execute(CREATE_RUNS_TABLE_SQL)
                conn.cursor().execute(CREATE_RUN_TAGS_TABLE_SQL)
                conn.cursor().execute('PRAGMA journal_mode=WAL;')
        finally:
            conn.close()
        return SqliteRunStorage(conn_string, inst_data)

    @contextmanager
    def _connect(self):
        try:
            with sqlite3.connect(self.conn_string) as conn:
                yield conn
        finally:
            conn.close()

    def add_run(self, pipeline_run):
        check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)

        with self._connect() as conn:
            conn.cursor().execute(
                INSERT_RUN_SQL,
                (
                    pipeline_run.run_id,
                    pipeline_run.pipeline_name,
                    str(pipeline_run.status),
                    serialize_dagster_namedtuple(pipeline_run),
                ),
            )
            if pipeline_run.tags and len(pipeline_run.tags) > 0:
                conn.cursor().executemany(
                    INSERT_RUN_TAGS_SQL,
                    [(pipeline_run.run_id, k, v) for k, v in pipeline_run.tags.items()],
                )

        return pipeline_run

    def handle_run_event(self, run_id, event):
        check.str_param(run_id, 'run_id')
        check.inst_param(event, 'event', DagsterEvent)

        lookup = {
            DagsterEventType.PIPELINE_START: PipelineRunStatus.STARTED,
            DagsterEventType.PIPELINE_SUCCESS: PipelineRunStatus.SUCCESS,
            DagsterEventType.PIPELINE_FAILURE: PipelineRunStatus.FAILURE,
        }

        if event.event_type not in lookup:
            return

        run = self.get_run_by_id(run_id)
        if not run:
            # TODO log?
            return

        SQL_UPDATE = '''
        UPDATE runs
        SET status = ?, run_body = ?, update_timestamp = ?
        WHERE run_id = ?
        '''

        new_pipeline_status = lookup[event.event_type]

        with self._connect() as conn:
            conn.cursor().execute(
                SQL_UPDATE,
                (
                    str(new_pipeline_status),
                    serialize_dagster_namedtuple(run.run_with_status(new_pipeline_status)),
                    datetime.now(),
                    run_id,
                ),
            )

    def _rows_to_runs(self, rows):
        return list(map(lambda r: deserialize_json_to_dagster_namedtuple(r[0]), rows))

    def all_runs(self):
        '''Return all the runs present in the storage.

        Returns:
            Iterable[(str, PipelineRun)]: Tuples of run_id, pipeline_run.
        '''

        with self._connect() as conn:
            rows = conn.cursor().execute('SELECT run_body FROM runs').fetchall()
            return self._rows_to_runs(rows)

    def all_runs_for_pipeline(self, pipeline_name):
        '''Return all the runs present in the storage for a given pipeline.

        Args:
            pipeline_name (str): The pipeline to index on

        Returns:
            Iterable[(str, PipelineRun)]: Tuples of run_id, pipeline_run.
        '''
        check.str_param(pipeline_name, 'pipeline_name')

        with self._connect() as conn:
            rows = (
                conn.cursor()
                .execute('SELECT run_body FROM runs WHERE pipeline_name = ?', (pipeline_name,))
                .fetchall()
            )
            return self._rows_to_runs(rows)

    def get_run_by_id(self, run_id):
        '''Get a run by its id.

        Args:
            run_id (str): The id of the run

        Returns:
            Optional[PipelineRun]
        '''
        check.str_param(run_id, 'run_id')

        with self._connect() as conn:
            rows = (
                conn.cursor()
                .execute('SELECT run_body FROM runs WHERE run_id = ?', (run_id,))
                .fetchall()
            )
            return deserialize_json_to_dagster_namedtuple(rows[0][0]) if len(rows) else None

    def all_runs_for_tag(self, key, value):
        with self._connect() as conn:
            rows = (
                conn.cursor()
                .execute(
                    '''
                    SELECT run_body
                    FROM runs
                    INNER JOIN run_tags
                    ON runs.run_id = run_tags.run_id
                    WHERE run_tags.key = ? AND run_tags.value = ?
                    ''',
                    (key, value),
                )
                .fetchall()
            )
            return self._rows_to_runs(rows)

    def has_run(self, run_id):
        check.str_param(run_id, 'run_id')
        return bool(self.get_run_by_id(run_id))

    def wipe(self):
        '''Clears the run storage.'''
        with self._connect() as conn:
            conn.cursor().execute(DELETE_RUNS_SQL)
            conn.cursor().execute(DELETE_RUN_TAGS_SQL)
