from typing import Dict, List, NamedTuple, Optional

from dagster import check
from dagster.utils import merge_dicts

from ..definitions.executor_definition import ExecutorDefinition
from ..definitions.resource_definition import ResourceDefinition
from ..errors import DagsterInvalidDefinitionError
from .asset import AssetsDefinition
from .assets_job import build_root_manager, build_source_assets_by_key
from .foreign_asset import ForeignAsset


class AssetCollection(
    NamedTuple(
        "_AssetCollection",
        [
            ("assets", List[AssetsDefinition]),
            ("source_assets", List[ForeignAsset]),
            ("resource_defs", Dict[str, ResourceDefinition]),
            ("executor_def", Optional[ExecutorDefinition]),
        ],
    )
):
    def __new__(
        cls,
        assets: List[AssetsDefinition],
        source_assets: List[ForeignAsset],
        resource_defs: Dict[str, ResourceDefinition],
        executor_def: Optional[ExecutorDefinition],
    ):
        source_assets_by_key = build_source_assets_by_key(source_assets)
        root_manager = build_root_manager(source_assets_by_key)

        resource_defs = merge_dicts(resource_defs, {"root_manager": root_manager})

        _validate_resource_reqs_for_asset_collection(
            asset_list=assets, source_assets=source_assets, resource_defs=resource_defs
        )

        return super(AssetCollection, cls).__new__(
            cls,
            assets=assets,
            source_assets=source_assets,
            resource_defs=resource_defs,
            executor_def=executor_def,
        )

    @staticmethod
    def from_list(
        assets: List[AssetsDefinition],
        source_assets: Optional[List[ForeignAsset]] = None,
        resource_defs: Optional[Dict[str, ResourceDefinition]] = None,
        executor_def: Optional[ExecutorDefinition] = None,
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


def _validate_resource_reqs_for_asset_collection(
    asset_list: List[AssetsDefinition],
    source_assets: List[ForeignAsset],
    resource_defs: Dict[str, ResourceDefinition],
):
    present_resource_keys = set(resource_defs.keys())
    for asset_def in asset_list:
        resource_keys = set(asset_def.op.required_resource_keys or {})
        missing_resource_keys = list(set(resource_keys) - present_resource_keys)
        if missing_resource_keys:
            raise DagsterInvalidDefinitionError(
                f"AssetCollection is missing required resource keys for asset '{asset_def.op.name}'. Missing resource keys: {missing_resource_keys}"
            )

        for asset_key, input_def in asset_def.input_defs_by_asset_key.items():
            if (
                input_def.root_manager_key
                and input_def.root_manager_key not in present_resource_keys
            ):
                raise DagsterInvalidDefinitionError(
                    f"The input associated with AssetKey '{asset_key}' requires root input manager '{input_def.root_manager_key}' but was not provided on asset collection. Provided resources: {list(present_resource_keys)}"
                )

    for source_asset in source_assets:
        if source_asset.io_manager_key and source_asset.io_manager_key not in present_resource_keys:
            raise DagsterInvalidDefinitionError(
                f"SourceAsset with key {source_asset.key} requires io manager with key '{source_asset.io_manager_key}', but was not provided on AssetCollection. Provided keys: {list(present_resource_keys)}"
            )

    for resource_key, resource_def in resource_defs.items():
        resource_keys = set(resource_def.required_resource_keys)
        missing_resource_keys = list(set(resource_keys) - present_resource_keys)
        if missing_resource_keys:
            raise DagsterInvalidDefinitionError(
                f"AssetCollection is missing required resource keys for resource '{resource_key}'. Missing resource keys: {missing_resource_keys}"
            )
