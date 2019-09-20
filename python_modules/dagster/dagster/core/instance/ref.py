import os
from abc import ABCMeta
from collections import namedtuple

import six
import yaml

from dagster import check
from dagster.core.serdes import ConfigurableClassData, whitelist_for_serdes

from .config import dagster_feature_set


def _runs_directory(base):
    return os.path.join(base, 'history', 'runs', '')


class InstanceRef(six.with_metaclass(ABCMeta)):
    pass


@whitelist_for_serdes
class LocalInstanceRef(
    namedtuple(
        '_LocalInstanceRef',
        'feature_set root_storage_data run_storage_data event_storage_data compute_logs_data',
    ),
    InstanceRef,
):
    def __new__(
        self,
        feature_set,
        root_storage_data,
        run_storage_data,
        event_storage_data,
        compute_logs_data=None,
    ):
        return super(self, LocalInstanceRef).__new__(
            self,
            feature_set=check.opt_list_param(feature_set, 'feature_set'),
            root_storage_data=check.inst_param(
                root_storage_data, 'root_storage_data', ConfigurableClassData
            ),
            run_storage_data=check.inst_param(
                run_storage_data, 'run_storage_data', ConfigurableClassData
            ),
            event_storage_data=check.inst_param(
                event_storage_data, 'event_storage_data', ConfigurableClassData
            ),
            compute_logs_data=check.opt_inst_param(
                compute_logs_data, 'compute_logs_data', ConfigurableClassData
            ),
        )

    @staticmethod
    def from_root_storage_dir(root_storage_dir):
        return LocalInstanceRef(
            feature_set=dagster_feature_set(root_storage_dir),
            root_storage_data=ConfigurableClassData(
                'dagster.core.storage.root',
                'RootStorage',
                yaml.dump({'root_storage_dir': root_storage_dir}, default_flow_style=False),
            ),
            run_storage_data=ConfigurableClassData(
                'dagster.core.storage.runs',
                'FilesystemRunStorage',
                yaml.dump(
                    {'base_dir': _runs_directory(root_storage_dir)}, default_flow_style=False
                ),
            ),
            event_storage_data=ConfigurableClassData(
                'dagster.core.storage.event_log',
                'FilesystemEventLogStorage',
                yaml.dump(
                    {'base_dir': _runs_directory(root_storage_dir)}, default_flow_style=False
                ),
            ),
        )

    @property
    def root_storage(self):
        return self.root_storage_data.rehydrate()

    @property
    def run_storage(self):
        return self.run_storage_data.rehydrate()

    @property
    def event_storage(self):
        return self.event_storage_data.rehydrate()


class RemoteInstanceRef(
    namedtuple('_RemoteInstanceRef', 'root_storage_data event_storage_config run_storage_config'),
    InstanceRef,
):
    def __new__(self, root_storage_data, event_storage_config, run_storage_config):
        return super(self, RemoteInstanceRef).__new__(
            self,
            root_storage_data=check.inst_param(
                root_storage_data, 'root_storage_data', ConfigurableClassData
            ),
            event_storage_data=check.inst_param(
                event_storage_config, 'event_storage_data', ConfigurableClassData
            ),
            run_storage_data=check.inst_param(
                run_storage_config, 'run_storage_data', ConfigurableClassData
            ),
        )
