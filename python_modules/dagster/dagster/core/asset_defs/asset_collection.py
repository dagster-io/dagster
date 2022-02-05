from typing import Dict, List, NamedTuple, Optional

from ..definitions.resource_definition import ResourceDefinition
from .asset import AssetsDefinition
from ..definitions.executor_definition import ExecutorDefinition


class AssetCollection(NamedTuple):
    assets: List[AssetsDefinition]
    resource_defs: Dict[str, ResourceDefinition]

    @staticmethod
    def from_list(assets, resource_defs=None) -> "AssetCollection":
        return AssetCollection(assets=assets, resource_defs=resource_defs)

    @staticmethod
    def from_package(path, resource_defs=None) -> "AssetCollection":
        pass

    def execute_in_process(self, instance):
        pass

    def build_job_spec(self, name, subset, executor_def=None):
        # TODO: resolve subset immediately using the asset list and make sure it doesn't error
        return JobSpec(name=name, subset=subset, executor_def=executor_def)

    def build_schedule(self):
        pass

    def build_sensor(self):
        pass


class JobSpec(NamedTuple):
    name: str
    subset: str
    executor_def: ExecutorDefinition