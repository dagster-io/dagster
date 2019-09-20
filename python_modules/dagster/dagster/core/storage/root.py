import os

from dagster import check
from dagster.core.definitions.environment_configs import SystemNamedDict
from dagster.core.serdes import ConfigurableClass
from dagster.core.types import Field, String


class RootStorage(ConfigurableClass):
    def __init__(self, root_storage_dir, inst_data=None):
        self._root_storage_dir = root_storage_dir
        super(RootStorage, self).__init__(inst_data=inst_data)

    @property
    def root_storage_dir(self):
        return self._root_storage_dir

    def file_manager_dir(self, run_id):
        check.str_param(run_id, 'run_id')
        return os.path.join(self.root_storage_dir, 'storage', run_id, 'files')

    def intermediates_dir(self, run_id):
        return os.path.join(self.root_storage_dir, 'storage', run_id, '')

    @property
    def schedules_dir(self):
        return os.path.join(self.root_storage_dir, 'schedules')

    @staticmethod
    def from_config_value(config_value, **kwargs):
        return RootStorage(**dict(config_value, **kwargs))

    @classmethod
    def config_type(cls):
        return SystemNamedDict('RootStorageConfig', {'root_storage_dir': Field(String)})
