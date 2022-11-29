import warnings
from collections import deque
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Dict,
    Iterator,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Union,
)

import toposort

import dagster._check as check
from dagster._core.errors import DagsterInvalidInvocationError, DagsterInvariantViolationError
from dagster._core.selector.subset_selector import DependencyGraph, generate_asset_dep_graph

from .assets import AssetsDefinition
from .events import AssetKey, AssetKeyPartitionKey
from .freshness_policy import FreshnessPolicy
from .partition import PartitionsDefinition
from .partition_key_range import PartitionKeyRange
from .partition_mapping import PartitionMapping, infer_partition_mapping
from .source_asset import SourceAsset
from .time_window_partitions import TimeWindowPartitionsDefinition

if TYPE_CHECKING:
    from dagster._core.host_representation.external_data import ExternalAssetNode


class AssetGraph(
    NamedTuple(
        "_AssetGraph",
        [
            ("asset_dep_graph", DependencyGraph),
            ("source_asset_keys", AbstractSet[AssetKey]),
            ("partitions_defs_by_key", Mapping[AssetKey, Optional[PartitionsDefinition]]),
            (
                "partition_mappings_by_key",
                Optional[Mapping[AssetKey, Optional[Mapping[AssetKey, PartitionMapping]]]],
            ),
            ("group_names_by_key", Mapping[AssetKey, Optional[str]]),
            ("freshness_policies_by_key", Mapping[AssetKey, Optional[FreshnessPolicy]]),
        ],
    )
):
    def __new__(
        cls,
        asset_dep_graph: DependencyGraph,
        source_asset_keys: AbstractSet[AssetKey],
        partitions_defs_by_key: Mapping[AssetKey, Optional[PartitionsDefinition]],
        partition_mappings_by_key: Optional[
            Mapping[AssetKey, Optional[Mapping[AssetKey, PartitionMapping]]]
        ],
        group_names_by_key: Mapping[AssetKey, Optional[str]],
        freshness_policies_by_key: Mapping[AssetKey, Optional[FreshnessPolicy]],
    ):
        return super(AssetGraph, cls).__new__(
            cls,
            asset_dep_graph=asset_dep_graph,
            source_asset_keys=source_asset_keys,
            partitions_defs_by_key=partitions_defs_by_key,
            partition_mappings_by_key=partition_mappings_by_key,
            group_names_by_key=group_names_by_key,
            freshness_policies_by_key=freshness_policies_by_key,
        )

    @staticmethod
    def from_assets(all_assets: Sequence[Union[AssetsDefinition, SourceAsset]]) -> "AssetGraph":
        assets_defs = []
        source_assets = []
        partitions_defs_by_key: Dict[AssetKey, Optional[PartitionsDefinition]] = {}
        partition_mappings_by_key: Dict[
            AssetKey, Optional[Mapping[AssetKey, PartitionMapping]]
        ] = {}
        group_names_by_key: Dict[AssetKey, Optional[str]] = {}
        freshness_policies_by_key: Dict[AssetKey, Optional[FreshnessPolicy]] = {}

        for asset in all_assets:
            if isinstance(asset, SourceAsset):
                source_assets.append(asset)
            elif isinstance(asset, AssetsDefinition):
                assets_defs.append(asset)
                partition_mappings_by_key.update(
                    {
                        key: asset._partition_mappings  # pylint: disable=protected-access
                        for key in asset.keys
                    }
                )
                partitions_defs_by_key.update({key: asset.partitions_def for key in asset.keys})
                group_names_by_key.update(asset.group_names_by_key)
                freshness_policies_by_key.update(asset.freshness_policies_by_key)
            else:
                check.failed(f"Expected SourceAsset or AssetsDefinition, got {type(asset)}")
        return AssetGraph(
            asset_dep_graph=generate_asset_dep_graph(assets_defs, source_assets),
            source_asset_keys={source_asset.key for source_asset in source_assets},
            partitions_defs_by_key=partitions_defs_by_key,
            partition_mappings_by_key=partition_mappings_by_key,
            group_names_by_key=group_names_by_key,
            freshness_policies_by_key=freshness_policies_by_key,
        )

    @staticmethod
    def from_external_assets(external_asset_nodes: Sequence["ExternalAssetNode"]) -> "AssetGraph":
        upstream = {}
        downstream = {}
        source_asset_keys = set()
        partitions_defs_by_key = {}
        group_names_by_key = {}
        freshness_policies_by_key = {}

        for node in external_asset_nodes:
            if node.is_source:
                source_asset_keys.add(node.asset_key)
            upstream[node.asset_key] = {dep.upstream_asset_key for dep in node.dependencies}
            downstream[node.asset_key] = {dep.downstream_asset_key for dep in node.depended_by}
            partitions_defs_by_key[node.asset_key] = (
                node.partitions_def_data.get_partitions_definition()
                if node.partitions_def_data
                else None
            )
            group_names_by_key[node.asset_key] = node.group_name
            freshness_policies_by_key[node.asset_key] = node.freshness_policy

        return AssetGraph(
            asset_dep_graph={"upstream": upstream, "downstream": downstream},
            source_asset_keys=source_asset_keys,
            partitions_defs_by_key=partitions_defs_by_key,
            partition_mappings_by_key=None,
            group_names_by_key=group_names_by_key,
            freshness_policies_by_key=freshness_policies_by_key,
        )

    @property
    def all_asset_keys(self) -> AbstractSet[AssetKey]:
        return self.asset_dep_graph["upstream"].keys()

    def get_partitions_def(self, asset_key: AssetKey) -> Optional[PartitionsDefinition]:
        return self.partitions_defs_by_key.get(asset_key)

    def get_partition_mapping(
        self, asset_key: AssetKey, in_asset_key: AssetKey
    ) -> PartitionMapping:
        if self.partition_mappings_by_key is None:
            raise DagsterInvariantViolationError(
                "Partition mapping information not set when creating this AssetGraph"
            )
        partitions_def = self.get_partitions_def(asset_key)
        partition_mappings = self.partition_mappings_by_key.get(asset_key) or {}
        return infer_partition_mapping(partition_mappings.get(in_asset_key), partitions_def)

    def is_partitioned(self, asset_key: AssetKey) -> bool:
        return self.get_partitions_def(asset_key) is not None

    def have_same_partitioning(self, asset_key1: AssetKey, asset_key2: AssetKey) -> bool:
        """Returns whether the given assets have the same partitions definition"""
        return self.get_partitions_def(asset_key1) == self.get_partitions_def(asset_key2)

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
        asset. Uses the existing partition mapping between the child asset and the parent asset.
        Args:
            parent_partition_key (Optional[str]): The partition key to convert.
            parent_asset_key (AssetKey): The asset key of the upstream asset, which the provided
                partition key belongs to.
            child_asset_key (AssetKey): The asset key of the downstream asset. The provided partition
                key will be mapped to partitions within this asset.
        Returns:
            Sequence[str]: A list of the corresponding downstream partitions in child_asset_key that
                partition_key maps to.
        """
        child_partitions_def = self.get_partitions_def(child_asset_key)
        parent_partitions_def = self.get_partitions_def(parent_asset_key)

        if child_partitions_def is None:
            raise DagsterInvalidInvocationError(
                f"Asset key {child_asset_key} is not partitioned. Cannot get partition keys."
            )
        if parent_partition_key is None:
            return child_partitions_def.get_partition_keys()

        if parent_partitions_def is None:
            raise DagsterInvalidInvocationError(
                "Parent partition key provided, but parent asset is not partitioned."
            )

        partition_mapping = self.get_partition_mapping(child_asset_key, parent_asset_key)
        downstream_partition_key_range = (
            partition_mapping.get_downstream_partitions_for_partition_range(
                PartitionKeyRange(parent_partition_key, parent_partition_key),
                downstream_partitions_def=child_partitions_def,
                upstream_partitions_def=parent_partitions_def,
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

        child_partitions_def = self.get_partitions_def(child_asset_key)
        parent_partitions_def = self.get_partitions_def(parent_asset_key)

        if parent_partitions_def is None:
            raise DagsterInvalidInvocationError(
                f"Asset key {parent_asset_key} is not partitioned. Cannot get partition keys."
            )

        partition_mapping = self.get_partition_mapping(child_asset_key, parent_asset_key)
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

    def has_non_source_parents(self, asset_key: AssetKey) -> bool:
        """Determines if an asset has any parents which are not source assets"""
        if asset_key in self.source_asset_keys:
            return False
        return bool(self.get_parents(asset_key) - self.source_asset_keys)

    def get_non_source_roots(self, asset_key: AssetKey) -> AbstractSet[AssetKey]:
        """Returns all assets upstream of the given asset which do not consume any other
        AssetsDefinitions (but may consume SourceAssets).
        """
        if not self.has_non_source_parents(asset_key):
            return {asset_key}
        return {
            key
            for key in self.upstream_key_iterator(asset_key)
            if not self.has_non_source_parents(key)
        }

    def upstream_key_iterator(self, asset_key: AssetKey) -> Iterator[AssetKey]:
        """Iterates through all asset keys which are upstream of the given key."""
        visited: Set[AssetKey] = set()
        queue = deque([asset_key])
        while queue:
            current_key = queue.popleft()
            if current_key in self.source_asset_keys:
                continue
            for parent_key in self.get_parents(current_key):
                if parent_key not in visited:
                    yield parent_key
                    queue.append(parent_key)
                    visited.add(parent_key)

    def toposort_asset_keys(self) -> Sequence[AbstractSet[AssetKey]]:
        return [
            {key for key in level} for level in toposort.toposort(self.asset_dep_graph["upstream"])
        ]

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return self is other
