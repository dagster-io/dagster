from typing import Dict, List, NamedTuple

from ..definitions.job_definition import JobDefinition
from ..definitions.resource_definition import ResourceDefinition
from .asset import AssetsDefinition
from .assets_job import build_assets_job, build_job_from_spec


class AssetCollection(
    NamedTuple(
        "_AssetCollection",
        [
            ("assets", List[AssetsDefinition]),
            ("resource_defs", Dict[str, ResourceDefinition]),
            ("inner_job", JobDefinition),
        ],
    )
):
    def __new__(cls, assets, resource_defs):
        return super(AssetCollection, cls).__new__(
            cls,
            assets=assets,
            resource_defs=resource_defs,
            inner_job=build_assets_job(
                "__REPOSITORY_MEGA_JOB", assets, resource_defs=resource_defs
            ),
        )

    @staticmethod
    def from_list(assets, resource_defs=None) -> "AssetCollection":
        return AssetCollection(assets=assets, resource_defs=resource_defs)

    @staticmethod
    def from_package(path, resource_defs=None) -> "AssetCollection":
        pass

    def execute_in_process(self, instance=None):
        return self.inner_job.execute_in_process(instance=instance)

    def build_job(self, name, subset, executor_def=None) -> JobDefinition:
        return build_job_from_spec(
            self.inner_job,
            subselection=subset,
            executor_def=executor_def,
            name=name,
        )
