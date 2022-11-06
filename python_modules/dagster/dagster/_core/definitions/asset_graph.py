import warnings
from typing import AbstractSet, Optional, Sequence, Union

import toposort

import dagster._check as check
from dagster._core.errors import DagsterInvalidInvocationError
from dagster._core.selector.subset_selector import generate_asset_dep_graph

from .assets import AssetsDefinition
from .events import AssetKey, AssetKeyPartitionKey
from .partition import PartitionsDefinition
from .partition_key_range import PartitionKeyRange
from .source_asset import SourceAsset
from .time_window_partitions import TimeWindowPartitionsDefinition


class AssetGraph:
    def __init__(self, all_assets: Sequence[Union[AssetsDefinition, SourceAsset]]):
        assets_defs = []
        source_assets = []
        for asset in all_assets:
            if isinstance(asset, SourceAsset):
                source_assets.append(asset)
            elif isinstance(asset, AssetsDefinition):
                assets_defs.append(asset)
            else:
                check.failed(f"Expected SourceAsset or AssetsDefinition, got {type(asset)}")

        self.assets_defs = assets_defs
        self.all_assets_by_key = {
            asset_key: assets_def for assets_def in assets_defs for asset_key in assets_def.keys
        }

        self.asset_dep_graph = generate_asset_dep_graph(assets_defs, source_assets)
        self.source_asset_keys = {source_asset.key for source_asset in source_assets}

    @property
    def all_asset_keys(self) -> AbstractSet[AssetKey]:
        return self.all_assets_by_key.keys()

    def is_partitioned(self, asset_key: AssetKey) -> bool:
        return self.all_assets_by_key[asset_key].partitions_def is not None

    def have_same_partitioning(self, asset_key1: AssetKey, asset_key2: AssetKey) -> bool:
        """Returns whether the given assets have the same partitions definition"""
        return (
            self.all_assets_by_key[asset_key1].partitions_def
            == self.all_assets_by_key[asset_key2].partitions_def
        )

    def get_partitions_def(self, asset_key: AssetKey) -> Optional[PartitionsDefinition]:
        return self.all_assets_by_key[asset_key].partitions_def

    def get_children(self, asset_key: AssetKey) -> AbstractSet[AssetKey]:
        """Returns all assets that depend on the given asset"""
        return self.asset_dep_graph["downstream"][asset_key]

    def get_parents(self, asset_key: AssetKey) -> AbstractSet[AssetKey]:
        """Returns all assets that the given asset depends on"""
        return self.asset_dep_graph["upstream"][asset_key]

    def get_children_partitions(
        self, asset_key: AssetKey, partition_key: Optional[str] = None
    ) -> AbstractSet[AssetKeyPartitionKey]:
        """
        Returns every partition in every of the given asset's children that depends on the given
        partition of that asset.
        """
        result = set()

        for child_asset_key in self.get_children(asset_key):
            if self.is_partitioned(child_asset_key):
                for child_partition_key in self.get_child_partition_keys_of_parent(
                    partition_key, asset_key, child_asset_key
                ):
                    result.add(AssetKeyPartitionKey(child_asset_key, child_partition_key))
            else:
                result.add(AssetKeyPartitionKey(child_asset_key))

        return result

    def get_child_partition_keys_of_parent(
        self,
        parent_partition_key: Optional[str],
        parent_asset_key: AssetKey,
        child_asset_key: AssetKey,
    ) -> Sequence[str]:
        """
        Converts a partition key from one asset to the corresponding partition keys in a downstream
        asset. Uses the existing partition mapping between the child asset and the parent
        asset.

        Args:
            partition_key (Optional[str]): The partition key to convert.
            parent_asset_key (AssetKey): The asset key of the upstream asset, which the provided
                partition key belongs to.
            child_asset_key (AssetKey): The asset key of the downstream asset. The provided partition
                key will be mapped to partitions within this asset.

        Returns:
            Sequence[str]: A list of the corresponding downstream partitions in child_asset_key that
                partition_key maps to.
        """
        child_asset = self.all_assets_by_key[child_asset_key]
        parent_asset = self.all_assets_by_key[parent_asset_key]

        child_partitions_def = child_asset.partitions_def

        if child_partitions_def is None:
            raise DagsterInvalidInvocationError(
                f"Asset key {child_asset_key} is not partitioned. Cannot get partition keys."
            )

        if parent_partition_key is None:
            return child_partitions_def.get_partition_keys()

        if parent_asset.partitions_def is None:
            raise DagsterInvalidInvocationError(
                "Parent partition key provided, but parent asset is not partitioned."
            )

        partition_mapping = child_asset.get_partition_mapping(parent_asset_key)
        downstream_partition_key_range = (
            partition_mapping.get_downstream_partitions_for_partition_range(
                PartitionKeyRange(parent_partition_key, parent_partition_key),
                downstream_partitions_def=child_partitions_def,
                upstream_partitions_def=parent_asset.partitions_def,
            )
        )

        partition_keys = child_partitions_def.get_partition_keys()
        if (
            downstream_partition_key_range.start not in partition_keys
            or downstream_partition_key_range.end not in partition_keys
        ):
            error_msg = f"""Mapped partition key {parent_partition_key} to downstream partition key range
            [{downstream_partition_key_range.start}...{downstream_partition_key_range.end}] which
            is not a valid range in the downstream partitions definition."""

            if not isinstance(child_partitions_def, TimeWindowPartitionsDefinition):
                raise DagsterInvalidInvocationError(error_msg)
            else:
                warnings.warn(error_msg)

        return child_partitions_def.get_partition_keys_in_range(downstream_partition_key_range)

    def get_parents_partitions(
        self, asset_key: AssetKey, partition_key: Optional[str] = None
    ) -> AbstractSet[AssetKeyPartitionKey]:
        """
        Returns every partition in every of the given asset's parents that the given partition of
        that asset depends on.
        """
        result = set()

        for parent_asset_key in self.get_parents(asset_key):
            if self.is_partitioned(parent_asset_key):
                for parent_partition_key in self.get_parent_partition_keys_for_child(
                    partition_key, parent_asset_key, asset_key
                ):
                    result.add(AssetKeyPartitionKey(parent_asset_key, parent_partition_key))
            else:
                result.add(AssetKeyPartitionKey(parent_asset_key))

        return result

    def get_parent_partition_keys_for_child(
        self, partition_key: Optional[str], parent_asset_key: AssetKey, child_asset_key: AssetKey
    ) -> Sequence[str]:
        """
        Converts a partition key from one asset to the corresponding partition keys in one of its
        parent assets. Uses the existing partition mapping between the child asset and the parent
        asset.

        Args:
            partition_key (Optional[str]): The partition key to convert.
            child_asset_key (AssetKey): The asset key of the child asset, which the provided
                partition key belongs to.
            parent_asset_key (AssetKey): The asset key of the parent asset. The provided partition
                key will be mapped to partitions within this asset.

        Returns:
            Sequence[str]: A list of the corresponding downstream partitions in child_asset_key that
                partition_key maps to.
        """
        partition_key = check.opt_str_param(partition_key, "partition_key")

        child_asset = self.all_assets_by_key[child_asset_key]
        parent_asset = self.all_assets_by_key[parent_asset_key]

        child_partitions_def = child_asset.partitions_def
        parent_partitions_def = parent_asset.partitions_def

        if parent_partitions_def is None:
            raise DagsterInvalidInvocationError(
                f"Asset key {parent_asset_key} is not partitioned. Cannot get partition keys."
            )

        partition_mapping = child_asset.get_partition_mapping(parent_asset_key)
        upstream_partition_key_range = (
            partition_mapping.get_upstream_partitions_for_partition_range(
                PartitionKeyRange(partition_key, partition_key) if partition_key else None,
                downstream_partitions_def=child_partitions_def,
                upstream_partitions_def=parent_partitions_def,
            )
        )

        partition_keys = parent_partitions_def.get_partition_keys()
        if (
            upstream_partition_key_range.start not in partition_keys
            or upstream_partition_key_range.end not in partition_keys
        ):
            error_msg = f"""Mapped partition key {partition_key} to upstream partition key range
            [{upstream_partition_key_range.start}...{upstream_partition_key_range.end}] which
            is not a valid range in the upstream partitions definition."""

            if not isinstance(child_partitions_def, TimeWindowPartitionsDefinition):
                raise DagsterInvalidInvocationError(error_msg)
            else:
                warnings.warn(error_msg)

        return parent_partitions_def.get_partition_keys_in_range(upstream_partition_key_range)

    def toposort_asset_keys(self) -> Sequence[AbstractSet[AssetKey]]:
        return [
            {key for key in level} for level in toposort.toposort(self.asset_dep_graph["upstream"])
        ]
