from abc import ABCMeta, abstractmethod
from collections import namedtuple, OrderedDict
import json
import os
import shutil

import six

from dagster import check, seven
from dagster.utils import mkdir_p, list_pull


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
