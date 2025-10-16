from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, NamedTuple, Optional, Union

import dagster._check as check
from dagster._annotations import PublicAttr, public
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.partitions.mapping import PartitionMapping
from dagster._core.definitions.partitions.utils import warn_if_partition_mapping_not_builtin
from dagster._core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster._utils.warnings import deprecation_warning

if TYPE_CHECKING:
    from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
    from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
    from dagster._core.definitions.source_asset import SourceAsset


CoercibleToAssetDep = Union[
    CoercibleToAssetKey, "AssetSpec", "AssetsDefinition", "SourceAsset", "AssetDep"
]


@public
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

    Args:
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
        asset: Union[CoercibleToAssetKey, "AssetSpec", "AssetsDefinition", "SourceAsset"],
        *,
        partition_mapping: Optional[PartitionMapping] = None,
    ):
        from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
        from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
        from dagster._core.definitions.source_asset import SourceAsset

        if isinstance(asset, list):
            check.list_param(asset, "asset", of_type=str)
        else:
            check.inst_param(
                asset, "asset", (AssetKey, str, AssetSpec, AssetsDefinition, SourceAsset)
            )
        if isinstance(asset, AssetsDefinition) and len(asset.keys) > 1:
            # Only AssetsDefinition with a single asset can be passed
            raise DagsterInvalidDefinitionError(
                "Cannot create an AssetDep from a multi_asset AssetsDefinition."
                " Instead, specify dependencies on the assets created by the multi_asset"
                f" via AssetKeys or strings. For the multi_asset {asset.node_def.name}, the"
                f" available keys are: {asset.keys}."
            )

        asset_key = _get_asset_key(asset)

        if partition_mapping:
            warn_if_partition_mapping_not_builtin(partition_mapping)

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
    def from_coercible(arg: "CoercibleToAssetDep") -> "AssetDep":
        # if arg is AssetDep, return the original object to retain partition_mapping
        return arg if isinstance(arg, AssetDep) else AssetDep(asset=arg)


def _get_asset_key(arg: "CoercibleToAssetDep") -> AssetKey:
    from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
    from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
    from dagster._core.definitions.source_asset import SourceAsset

    if isinstance(arg, (AssetsDefinition, SourceAsset, AssetSpec)):
        return arg.key
    elif isinstance(arg, AssetDep):
        return arg.asset_key
    else:
        return AssetKey.from_coercible(arg)


def coerce_to_deps_and_check_duplicates(
    coercible_to_asset_deps: Optional[Iterable["CoercibleToAssetDep"]],
    key: Optional[Union[AssetKey, AssetCheckKey]],
) -> Sequence[AssetDep]:
    from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition

    if not coercible_to_asset_deps:
        return []

    # when AssetKey was a plain NamedTuple, it also happened to be Iterable[CoercibleToAssetKey]
    # so continue to support it here
    if isinstance(coercible_to_asset_deps, AssetKey):
        deprecation_warning(
            subject="Passing a single AssetKey to deps",
            breaking_version="1.10.0",
        )
        coercible_to_asset_deps = [coercible_to_asset_deps]

    # expand any multi_assets into a list of keys
    all_deps = []
    for dep in coercible_to_asset_deps:
        if isinstance(dep, AssetsDefinition) and len(dep.keys) > 1:
            all_deps.extend(dep.keys)
        else:
            all_deps.append(dep)

    dep_set = {}
    for dep in all_deps:
        asset_dep = AssetDep.from_coercible(dep)

        # we cannot do deduplication via a set because MultiPartitionMappings have an internal
        # dictionary that cannot be hashed. Instead deduplicate by making a dictionary and checking
        # for existing keys. If an asset is specified as a dependency more than once, only error if the
        # dependency is different (ie has a different PartitionMapping)
        if asset_dep.asset_key in dep_set and asset_dep != dep_set[asset_dep.asset_key]:
            key_msg = f"for spec {key}." if key else "per asset."
            raise DagsterInvariantViolationError(
                f"Cannot set a dependency on asset {asset_dep.asset_key} more than once {key_msg}"
            )
        dep_set[asset_dep.asset_key] = asset_dep

    return list(dep_set.values())
