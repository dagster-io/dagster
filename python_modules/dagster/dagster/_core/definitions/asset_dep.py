from typing import NamedTuple, Optional, Union

import dagster._check as check
from dagster._annotations import PublicAttr, experimental
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.partition_mapping import PartitionMapping
from dagster._core.definitions.source_asset import SourceAsset

from .events import (
    AssetKey,
    CoercibleToAssetKey,
)


@experimental
class AssetDep(
    NamedTuple(
        "_AssetDep",
        [
            ("asset_key", PublicAttr[AssetKey]),
            ("partition_mapping", PublicAttr[Optional[PartitionMapping]]),
        ],
    )
):
    """TODO - docs."""

    def __new__(
        cls,
        asset: Union[CoercibleToAssetKey, AssetSpec, AssetsDefinition, SourceAsset],
        partition_mapping: Optional[PartitionMapping] = None,
    ):
        if isinstance(asset, AssetSpec):
            asset_key = asset.asset_key
        else:
            asset_key = AssetKey.from_coercible_or_definition(asset)

        return super().__new__(
            cls,
            asset_key=asset_key,
            partition_mapping=check.opt_inst_param(
                partition_mapping,
                "partition_mapping",
                PartitionMapping,
            ),
        )
