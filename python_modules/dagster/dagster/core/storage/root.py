import os

from dagster import check
from dagster.core.definitions.environment_configs import SystemNamedDict
from dagster.core.serdes import ConfigurableClass, ConfigurableClassData
from dagster.core.types import Field, String


class LocalArtifactStorage(ConfigurableClass):
    def __init__(self, base_dir, inst_data=None):
        self._base_dir = base_dir
        self._inst_data = check.opt_inst_param(inst_data, 'inst_data', ConfigurableClassData)

    @property
    def inst_data(self):
        return self._inst_data

    @property
    def base_dir(self):
        return self._base_dir

    def file_manager_dir(self, run_id):
        check.str_param(run_id, 'run_id')
        return os.path.join(self.base_dir, 'storage', run_id, 'files')

    def intermediates_dir(self, run_id):
        return os.path.join(self.base_dir, 'storage', run_id, '')

    @property
    def schedules_dir(self):
        return os.path.join(self.base_dir, 'schedules')

    @staticmethod
    def from_config_value(inst_data, config_value, **kwargs):
        return LocalArtifactStorage(inst_data=inst_data, **dict(config_value, **kwargs))

    @classmethod
    def config_type(cls):
        return SystemNamedDict('LocalArtifactStorageConfig', {'base_dir': Field(String)})
