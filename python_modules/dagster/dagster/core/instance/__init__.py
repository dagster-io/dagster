import configparser
import os
from abc import ABCMeta
from collections import defaultdict, namedtuple
from enum import Enum

import six
from rx import Observable

from dagster import check, seven
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.storage.pipeline_run import PipelineRun

from .features import DagsterFeatures


def _is_dagster_home_set():
    return bool(os.getenv('DAGSTER_HOME'))


def _dagster_config(base_dir):
    config = configparser.ConfigParser(allow_no_value=True)

    config_path = os.path.join(base_dir, "dagster.cfg")
    if os.path.exists(config_path):
        config.read(config_path)

    return config


def _dagster_feature_set(base_dir):
    config = _dagster_config(base_dir)
    if config.has_section('FEATURES'):
        return {k for k, _ in config.items('FEATURES')}
    return None


def _dagster_home_dir():
    dagster_home_path = os.getenv('DAGSTER_HOME')

    if not dagster_home_path:
        raise DagsterInvariantViolationError(
            'DAGSTER_HOME is not set, check is_dagster_home_set before invoking.'
        )

    return os.path.expanduser(dagster_home_path)


class InstanceType(Enum):
    LOCAL = 'LOCAL'
    EPHEMERAL = 'EPHEMERAL'
    # REMOTE = 'REMOTE'


class InstanceRef(six.with_metaclass(ABCMeta)):
    pass


class LocalInstanceRef(namedtuple('_InstanceRef', 'home_dir'), InstanceRef):
    def __new__(self, home_dir):
        return super(self, LocalInstanceRef).__new__(
            self, home_dir=check.str_param(home_dir, 'home_dir')
        )


class DagsterInstance:
    _PROCESS_TEMPDIR = None

    def __init__(
        self, instance_type, root_storage_dir, run_storage, event_storage, feature_set=None
    ):
        from dagster.core.storage.event_log import EventLogStorage
        from dagster.core.storage.runs import RunStorage

        self._instance_type = check.inst_param(instance_type, 'instance_type', InstanceType)
        self._root_storage_dir = check.str_param(root_storage_dir, 'root_storage_dir')
        self._event_storage = check.inst_param(event_storage, 'event_storage', EventLogStorage)
        self._run_storage = check.inst_param(run_storage, 'run_storage', RunStorage)
        self._feature_set = check.opt_set_param(feature_set, 'feature_set', of_type=str)

        self._subscribers = defaultdict(list)

    def _load_history(self):
        historic_runs = self._run_storage.load_historic_runs()
        for run in historic_runs:
            if not run.is_finished:
                self.watch_event_logs(run.run_id, 0, self.handle_new_event)

    @staticmethod
    def ephemeral(tempdir=None):
        from dagster.core.storage.event_log import InMemoryEventLogStorage
        from dagster.core.storage.runs import InMemoryRunStorage

        if tempdir is None:
            tempdir = DagsterInstance.temp_storage()

        feature_set = _dagster_feature_set(tempdir)

        return DagsterInstance(
            InstanceType.EPHEMERAL,
            root_storage_dir=tempdir,
            run_storage=InMemoryRunStorage(),
            event_storage=InMemoryEventLogStorage(),
            feature_set=feature_set,
        )

    @staticmethod
    def get(fallback_storage=None):
        # 1. Use $DAGSTER_HOME to determine instance if set.
        if _is_dagster_home_set():
            # in the future we can read from config and create RemoteInstanceRef when needed
            return DagsterInstance.from_ref(LocalInstanceRef(_dagster_home_dir()))

        # 2. If that is not set use the fallback storage directory if provided.
        # This allows us to have a nice out of the box dagit experience where runs are persisted
        # across restarts in a tempdir that gets cleaned up when the dagit watchdog process exits.
        elif fallback_storage is not None:
            return DagsterInstance.from_ref(LocalInstanceRef(fallback_storage))

        # 3. If all else fails create an ephemeral in memory instance.
        else:
            return DagsterInstance.ephemeral(fallback_storage)

    @staticmethod
    def local_temp(tempdir=None, features=None):
        features = check.opt_set_param(features, 'features', str)
        if tempdir is None:
            tempdir = DagsterInstance.temp_storage()

        return DagsterInstance.from_ref(LocalInstanceRef(tempdir), features)

    @staticmethod
    def from_ref(instance_ref, fallback_feature_set=None):
        check.inst_param(instance_ref, 'instance_ref', InstanceRef)
        check.opt_set_param(fallback_feature_set, 'fallback_feature_set', str)

        if isinstance(instance_ref, LocalInstanceRef):
            from dagster.core.storage.event_log import FilesystemEventLogStorage
            from dagster.core.storage.runs import FilesystemRunStorage

            feature_set = _dagster_feature_set(instance_ref.home_dir) or fallback_feature_set

            return DagsterInstance(
                instance_type=InstanceType.LOCAL,
                root_storage_dir=instance_ref.home_dir,
                run_storage=FilesystemRunStorage(_runs_directory(instance_ref.home_dir)),
                event_storage=FilesystemEventLogStorage(_runs_directory(instance_ref.home_dir)),
                feature_set=feature_set,
            )

        else:
            check.failed('Unhandled instance type {}'.format(type(instance_ref)))

    def get_ref(self):
        if self._instance_type == InstanceType.LOCAL:
            return LocalInstanceRef(self._root_storage_dir)
        else:
            check.failed(
                'Can not take produce an instance reference for {t}'.format(t=self._instance_type)
            )

    @staticmethod
    def temp_storage():
        if DagsterInstance._PROCESS_TEMPDIR is None:
            DagsterInstance._PROCESS_TEMPDIR = seven.TemporaryDirectory()
        return DagsterInstance._PROCESS_TEMPDIR.name

    def root_directory(self):
        return self._root_storage_dir

    # features

    def is_feature_enabled(self, feature):
        check.inst_param(feature, 'feature', DagsterFeatures)
        return feature.value in self._feature_set

    # run storage

    def get_run(self, run_id):
        return self._run_storage.get_run_by_id(run_id)

    def create_empty_run(self, run_id, pipeline_name):
        pipeline_run = PipelineRun.create_empty_run(pipeline_name, run_id)
        return self._run_storage.add_run(pipeline_run)

    def create_run(self, pipeline_run):
        check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
        run_id = pipeline_run.run_id
        if self._run_storage.has_run(run_id):
            existing_run = self._run_storage.get_run_by_id(run_id)
            check.invariant(
                existing_run == pipeline_run,
                'Attempting to create a different pipeline run for an existing run id',
            )
            return existing_run

        return self._run_storage.add_run(pipeline_run)

    def has_run(self, run_id):
        return self._run_storage.has_run(run_id)

    @property
    def all_runs(self):
        return self._run_storage.all_runs

    def all_runs_for_pipeline(self, pipeline):
        return self._run_storage.all_runs_for_pipeline(pipeline)

    def wipe(self):
        self._run_storage.wipe()
        self._event_storage.wipe()

    # event storage

    def logs_after(self, run_id, cursor):
        return self._event_storage.get_logs_for_run(run_id, cursor=cursor)

    def all_logs(self, run_id):
        return self._event_storage.get_logs_for_run(run_id)

    def logs_ready(self, run_id):
        return self._event_storage.logs_ready(run_id)

    def watch_event_logs(self, run_id, cursor, cb):
        from dagster.core.storage.event_log import WatchableEventLogStorage

        check.invariant(
            isinstance(self._event_storage, WatchableEventLogStorage),
            'In order to call watch_event_logs the event_storage must be watchable',
        )
        return self._event_storage.watch(run_id, cursor, cb)

    # event subscriptions

    def handle_new_event(self, event):
        self._event_storage.store_event(event)
        run_id = event.run_id
        if event.is_dagster_event and event.dagster_event.is_pipeline_event:
            self._run_storage.handle_run_event(run_id, event.dagster_event)

        for sub in self._subscribers[run_id]:
            sub.handle_new_event(event)

    def subscribe(self, run_id, subscriber):
        self._subscribers[run_id].append(subscriber)

    # directories

    def file_manager_directory(self, run_id):
        return os.path.join(self._root_storage_dir, 'storage', run_id, 'files')

    def intermediates_directory(self, run_id):
        return os.path.join(self._root_storage_dir, 'storage', run_id, 'intermediates')

    def compute_logs_directory(self, run_id):
        return os.path.join(self._root_storage_dir, 'storage', run_id, 'compute_logs')

    def schedules_directory(self):
        return os.path.join(self._root_storage_dir, 'schedules')


def _runs_directory(base):
    return os.path.join(base, 'history', 'runs', '')
