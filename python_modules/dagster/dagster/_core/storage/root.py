import os
from typing import Optional

from typing_extensions import TypedDict

from dagster import (
    StringSource,
    _check as check,
)
from dagster._config.config_schema import UserConfigSchema
from dagster._serdes import ConfigurableClass, ConfigurableClassData


class LocalArtifactStorageConfig(TypedDict):
    base_dir: str


class LocalArtifactStorage(ConfigurableClass):
    def __init__(self, base_dir: str, inst_data: Optional[ConfigurableClassData] = None):
        self._base_dir = base_dir
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)

    @property
    def inst_data(self) -> Optional[ConfigurableClassData]:
        return self._inst_data

    @property
    def base_dir(self) -> str:
        return self._base_dir

    def file_manager_dir(self, run_id: str) -> str:
        check.str_param(run_id, "run_id")
        return os.path.join(self.base_dir, "storage", run_id, "files")

    @property
    def storage_dir(self) -> str:
        return os.path.join(self.base_dir, "storage")

    @property
    def schedules_dir(self) -> str:
        return os.path.join(self.base_dir, "schedules")

    @staticmethod
    def from_config_value(
        inst_data: Optional[ConfigurableClassData], config_value: LocalArtifactStorageConfig
    ) -> "LocalArtifactStorage":
        return LocalArtifactStorage(inst_data=inst_data, **config_value)

    @classmethod
    def config_type(cls) -> UserConfigSchema:
        return {"base_dir": StringSource}
