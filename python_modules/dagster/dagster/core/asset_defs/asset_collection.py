from typing import Dict, List, NamedTuple

from dagster import check

from ..definitions.executor_definition import ExecutorDefinition
from ..definitions.job_definition import JobDefinition
from ..definitions.resource_definition import ResourceDefinition
from .asset import AssetsDefinition
from .foreign_asset import ForeignAsset


class AssetCollection(
    NamedTuple(
        "_AssetCollection",
        [
            ("assets", List[AssetsDefinition]),
            ("source_assets", List[ForeignAsset]),
            ("resource_defs", Dict[str, ResourceDefinition]),
            ("executor_def", ExecutorDefinition),
        ],
    )
):
    def __new__(cls, assets, source_assets, resource_defs, executor_def):
        return super(AssetCollection, cls).__new__(
            cls,
            assets=assets,
            source_assets=source_assets,
            resource_defs=resource_defs,
            executor_def=executor_def,
        )

    @staticmethod
    def from_list(
        assets, source_assets=None, resource_defs=None, executor_def=None
    ) -> "AssetCollection":

        check.list_param(assets, "assets", of_type=AssetsDefinition)
        source_assets = check.opt_list_param(source_assets, "source_assets", of_type=ForeignAsset)
        resource_defs = check.opt_dict_param(
            resource_defs, "resource_defs", key_type=str, value_type=ResourceDefinition
        )
        executor_def = check.opt_inst_param(executor_def, "executor_def", ExecutorDefinition)

        return AssetCollection(
            assets=assets,
            source_assets=source_assets,
            resource_defs=resource_defs,
            executor_def=executor_def,
        )
