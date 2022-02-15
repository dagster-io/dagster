from typing import Mapping, NamedTuple, Optional, Sequence

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
            ("assets", Sequence[AssetsDefinition]),
            ("source_assets", Sequence[ForeignAsset]),
            ("resource_defs", Mapping[str, ResourceDefinition]),
            ("executor_def", Optional[ExecutorDefinition]),
        ],
    )
):
    def __new__(
        cls,
        assets: Sequence[AssetsDefinition],
        source_assets: Optional[Sequence[ForeignAsset]] = None,
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
        executor_def: Optional[ExecutorDefinition] = None,
    ):
        from dagster.core.definitions.graph_definition import default_job_io_manager

        check.list_param(assets, "assets", of_type=AssetsDefinition)
        source_assets = check.opt_list_param(source_assets, "source_assets", of_type=ForeignAsset)
        resource_defs = check.opt_dict_param(
            resource_defs, "resource_defs", key_type=str, value_type=ResourceDefinition
        )
        executor_def = check.opt_inst_param(executor_def, "executor_def", ExecutorDefinition)

        source_assets_by_key = build_source_assets_by_key(source_assets)
        root_manager = build_root_manager(source_assets_by_key)

        if "root_manager" in resource_defs:
            raise DagsterInvalidDefinitionError(
                "Resource dictionary included resource with key 'root_manager', which is a reserved resource keyword in Dagster. Please change this key, and then change all places that require this key to a new value."
            )
        # In the case of collisions, merge_dicts takes values from the dictionary latest in the list, so we place the user provided resource defs after the defaults.
        resource_defs = merge_dicts(
            {"root_manager": root_manager, "io_manager": default_job_io_manager},
            resource_defs,
        )

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

    @property
    def all_assets_job_name(self) -> str:
        """The name of the mega-job that the provided list of assets is coerced into."""
        return "__ASSET_COLLECTION"


def _validate_resource_reqs_for_asset_collection(
    asset_list: Sequence[AssetsDefinition],
    source_assets: Sequence[ForeignAsset],
    resource_defs: Mapping[str, ResourceDefinition],
):
    present_resource_keys = set(resource_defs.keys())
    for asset_def in asset_list:
        resource_keys = set(asset_def.op.required_resource_keys or {})
        missing_resource_keys = list(set(resource_keys) - present_resource_keys)
        if missing_resource_keys:
            raise DagsterInvalidDefinitionError(
                f"AssetCollection is missing required resource keys for asset '{asset_def.op.name}'. Missing resource keys: {missing_resource_keys}"
            )

        for asset_key, output_def in asset_def.output_defs_by_asset_key.items():
            if output_def.io_manager_key and output_def.io_manager_key not in present_resource_keys:
                raise DagsterInvalidDefinitionError(
                    f"Output '{output_def.name}' with AssetKey '{asset_key}' requires io manager '{output_def.io_manager_key}' but was not provided on asset collection. Provided resources: {sorted(list(present_resource_keys))}"
                )

    for source_asset in source_assets:
        if source_asset.io_manager_key and source_asset.io_manager_key not in present_resource_keys:
            raise DagsterInvalidDefinitionError(
                f"SourceAsset with key {source_asset.key} requires io manager with key '{source_asset.io_manager_key}', which was not provided on AssetCollection. Provided keys: {sorted(list(present_resource_keys))}"
            )

    for resource_key, resource_def in resource_defs.items():
        resource_keys = set(resource_def.required_resource_keys)
        missing_resource_keys = sorted(list(set(resource_keys) - present_resource_keys))
        if missing_resource_keys:
            raise DagsterInvalidDefinitionError(
                f"AssetCollection is missing required resource keys for resource '{resource_key}'. Missing resource keys: {missing_resource_keys}"
            )
