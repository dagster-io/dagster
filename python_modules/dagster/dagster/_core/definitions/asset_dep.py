from typing import NamedTuple, Optional, Union

import dagster._check as check
from dagster._annotations import PublicAttr, experimental
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.partition_mapping import PartitionMapping
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.errors import DagsterInvalidDefinitionError

from .events import (
    AssetKey,
    CoercibleToAssetKey,
)

CoercibleToAssetDep = Union[
    CoercibleToAssetKey, AssetSpec, AssetsDefinition, SourceAsset, "AssetDep"
]


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
    """Specifies a dependency on an upstream asset.

    Attributes:
        asset (Union[AssetKey, str, AssetSpec, AssetsDefinition, SourceAsset]): The upstream asset to depend on.
        partition_mapping (Optional[PartitionMapping]): Defines what partitions to depend on in
            the upstream asset. If not provided and the upstream asset is partitioned, defaults to
            the default partition mapping for the partitions definition, which is typically maps
            partition keys to the same partition keys in upstream assets.

    Examples:
    .. code-block:: python

        upstream_asset = AssetSpec("upstream_asset")
        downstream_asset = AssetSpec(
            "downstream_asset",
            deps=[
                AssetDep(
                    upstream_asset,
                    partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)
                )
            ]
        )
    """

    def __new__(
        cls,
        asset: CoercibleToAssetDep,
        partition_mapping: Optional[PartitionMapping] = None,
    ):
        if isinstance(asset, AssetsDefinition) and len(asset.keys) > 1:
            # Only AssetsDefinition with a single asset can be passed
            raise DagsterInvalidDefinitionError(
                "Cannot pass a multi_asset AssetsDefinition as an argument to deps."
                " Instead, specify dependencies on the assets created by the multi_asset"
                f" via AssetKeys or strings. For the multi_asset {asset.node_def.name}, the"
                f" available keys are: {asset.keys}."
            )

        asset_key = AssetKey.from_coercible_to_asset_dep(asset)

        return super().__new__(
            cls,
            asset_key=asset_key,
            partition_mapping=check.opt_inst_param(
                partition_mapping,
                "partition_mapping",
                PartitionMapping,
            ),
        )

    @staticmethod
    def from_coercible(arg: "CoercibleToAssetDep"):
        if isinstance(arg, AssetDep):
            # we need to retain the partition_mapping, so return the original object
            return arg
        return AssetDep(asset=arg)
