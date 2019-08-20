import json
import os
import shutil
from abc import ABCMeta, abstractmethod
from collections import OrderedDict, namedtuple

import six
import sqlite3


from dagster import check, seven
from dagster.utils import list_pull, mkdir_p


def base_runs_directory():
    return os.path.join(seven.get_system_temp_directory(), 'dagster', 'runs')


def base_directory_for_run(run_id):
    check.str_param(run_id, 'run_id')
    return os.path.join(base_runs_directory(), run_id)


def meta_file(base_dir):
    return os.path.join(base_dir, 'runmeta.jsonl')


class DagsterRunMeta(namedtuple('_DagsterRunMeta', 'run_id timestamp pipeline_name')):
    def __new__(cls, run_id, timestamp, pipeline_name):
        return super(DagsterRunMeta, cls).__new__(
            cls,
            check.str_param(run_id, 'run_id'),
            check.float_param(timestamp, 'timestamp'),
            check.str_param(pipeline_name, 'pipeline_name'),
        )


class RunStorage(six.with_metaclass(ABCMeta)):  # pylint: disable=no-init
    @abstractmethod
    def write_dagster_run_meta(self, dagster_run_meta):
        pass

    def has_run(self, run_id):
        check.str_param(run_id, 'run_id')
        return run_id in self.get_run_ids()

    @abstractmethod
    def get_run_ids(self):
        pass

    @abstractmethod
    def get_run_metas(self):
        pass

    @abstractmethod
    def get_run_meta(self, run_id):
        pass

    @abstractmethod
    def nuke(self):
        pass

    @property
    @abstractmethod
    def is_persistent(self):
        pass


class FileSystemRunStorage(RunStorage):
    def __init__(self, base_dir=None):
        self._base_dir = check.opt_str_param(base_dir, 'base_dir', base_runs_directory())
        mkdir_p(base_runs_directory())
        self._meta_file = meta_file(self._base_dir)

    def write_dagster_run_meta(self, dagster_run_meta):
        check.inst_param(dagster_run_meta, 'dagster_run_meta', DagsterRunMeta)

        run_dir = os.path.join(self._base_dir, dagster_run_meta.run_id)

        mkdir_p(run_dir)

        with open(self._meta_file, 'a+') as ff:
            ff.write(seven.json.dumps(dagster_run_meta._asdict()) + '\n')

    def get_run_ids(self):
        return list_pull(self.get_run_metas(), 'run_id')

    def get_run_meta(self, run_id):
        check.str_param(run_id, 'run_id')
        for run_meta in self.get_run_metas():
            if run_meta.run_id == run_id:
                return run_meta

        return None

    def get_run_metas(self):
        if not os.path.exists(self._meta_file):
            return []

        run_metas = []
        with open(self._meta_file, 'r') as ff:
            line = ff.readline()
            while line:
                raw_run_meta = json.loads(line)
                run_metas.append(
                    DagsterRunMeta(
                        run_id=raw_run_meta['run_id'],
                        timestamp=raw_run_meta['timestamp'],
                        pipeline_name=raw_run_meta['pipeline_name'],
                    )
                )
                line = ff.readline()

        return run_metas

    def nuke(self):
        shutil.rmtree(self._base_dir)

    @property
    def is_persistent(self):
        return True


class InMemoryRunStorage(RunStorage):
    def __init__(self):
        self._run_metas = OrderedDict()

    def write_dagster_run_meta(self, dagster_run_meta):
        check.inst_param(dagster_run_meta, 'dagster_run_meta', DagsterRunMeta)
        self._run_metas[dagster_run_meta.run_id] = dagster_run_meta

    def get_run_ids(self):
        return list_pull(self.get_run_metas(), 'run_id')

    def get_run_metas(self):
        return list(self._run_metas.values())

    def get_run_meta(self, run_id):
        check.str_param(run_id, 'run_id')
        return self._run_metas[run_id]

    def nuke(self):
        self._run_metas = OrderedDict()

    @property
    def is_persistent(self):
        return False


CREATE_RUNS_TABLE = '''
    CREATE TABLE IF NOT EXISTS runs (
        run_id varchar(255) NOT NULL,
        timestamp real NOT NULL,
        pipeline_name varchar(1023) NOT NULL
    )
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

    def write_dagster_run_meta(self, dagster_run_meta):
        INSERT_RUN_STATEMENT = '''
        INSERT INTO runs (run_id, timestamp, pipeline_name) VALUES (
            '{run_id}',
            '{timestamp}',
            '{pipeline_name}'
        )
        '''

        self.conn.execute(
            INSERT_RUN_STATEMENT.format(
                run_id=dagster_run_meta.run_id,
                timestamp=dagster_run_meta.timestamp,
                pipeline_name=dagster_run_meta.pipeline_name,
            )
        )

    def get_run_ids(self):
        return list_pull(self.get_run_metas(), 'run_id')

    def get_run_metas(self):
        raw_runs = (
            self.conn.cursor()
            .execute('SELECT run_id, timestamp, pipeline_name FROM runs')
            .fetchall()
        )
        return list(map(run_meta_from_row, raw_runs))

    def get_run_meta(self, run_id):
        sql = "SELECT run_id, timestamp, pipeline_name FROM runs WHERE run_id = '{run_id}'".format(
            run_id=run_id
        )

        return run_meta_from_row(self.conn.cursor().execute(sql).fetchone())

    def nuke(self):
        self.conn.execute('DELETE FROM runs')

    @property
    def is_persistent(self):
        return True


def run_meta_from_row(row):
    return DagsterRunMeta(row[0], row[1], row[2])
