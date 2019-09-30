import os

from dagster import check
from dagster.core.definitions.environment_configs import SystemNamedDict
from dagster.core.serdes import ConfigurableClass
from dagster.core.types import Field, String


class LocalArtifactStorage(ConfigurableClass):
    def __init__(self, base_dir, inst_data=None):
        self._base_dir = base_dir
        super(LocalArtifactStorage, self).__init__(inst_data=inst_data)

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
    def from_config_value(config_value, **kwargs):
        return LocalArtifactStorage(**dict(config_value, **kwargs))

    @classmethod
    def config_type(cls):
        return SystemNamedDict('LocalArtifactStorageConfig', {'base_dir': Field(String)})
