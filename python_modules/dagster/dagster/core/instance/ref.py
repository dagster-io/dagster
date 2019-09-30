import os
from collections import namedtuple

import yaml

from dagster import check
from dagster.core.serdes import ConfigurableClassData, whitelist_for_serdes

from .config import dagster_feature_set


def _runs_directory(base):
    return os.path.join(base, 'history', '')


def _event_logs_directory(base):
    return os.path.join(base, 'history', 'runs', '')


@whitelist_for_serdes
class InstanceRef(
    namedtuple(
        '_InstanceRef',
        'feature_set local_artifact_storage_data run_storage_data event_storage_data compute_logs_data',
    )
):
    def __new__(
        self,
        feature_set,
        local_artifact_storage_data,
        run_storage_data,
        event_storage_data,
        compute_logs_data=None,
    ):
        return super(self, InstanceRef).__new__(
            self,
            feature_set=check.opt_list_param(feature_set, 'feature_set'),
            local_artifact_storage_data=check.inst_param(
                local_artifact_storage_data, 'local_artifact_storage_data', ConfigurableClassData
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
    def from_dir(base_dir):
        return InstanceRef(
            feature_set=dagster_feature_set(base_dir),
            local_artifact_storage_data=ConfigurableClassData(
                'dagster.core.storage.root',
                'LocalArtifactStorage',
                yaml.dump({'base_dir': base_dir}, default_flow_style=False),
            ),
            run_storage_data=ConfigurableClassData(
                'dagster.core.storage.sqlite_run_storage',
                'SqliteRunStorage',
                yaml.dump({'base_dir': _runs_directory(base_dir)}, default_flow_style=False),
            ),
            event_storage_data=ConfigurableClassData(
                'dagster.core.storage.event_log',
                'SqliteEventLogStorage',
                yaml.dump({'base_dir': _event_logs_directory(base_dir)}, default_flow_style=False),
            ),
        )

    @property
    def local_artifact_storage(self):
        return self.local_artifact_storage_data.rehydrate()

    @property
    def run_storage(self):
        return self.run_storage_data.rehydrate()

    @property
    def event_storage(self):
        return self.event_storage_data.rehydrate()
