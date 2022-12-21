import functools
from collections import defaultdict, deque
from heapq import heapify, heappop, heappush
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Callable,
    Dict,
    Iterable,
    Iterator,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Union,
    cast,
)

import toposort

import dagster._check as check
from dagster._core.errors import DagsterInvalidInvocationError, DagsterInvariantViolationError
from dagster._core.selector.subset_selector import DependencyGraph, generate_asset_dep_graph

from .assets import AssetsDefinition
from .events import AssetKey, AssetKeyPartitionKey
from .freshness_policy import FreshnessPolicy
from .partition import PartitionsDefinition
from .partition_mapping import PartitionMapping, infer_partition_mapping
from .source_asset import SourceAsset
from .time_window_partitions import TimeWindowPartitionsDefinition

if TYPE_CHECKING:
    from dagster._core.host_representation.external_data import ExternalAssetNode


class AssetGraph(NamedTuple):
    asset_dep_graph: DependencyGraph
    source_asset_keys: AbstractSet[AssetKey]
    observable_source_asset_keys: AbstractSet[AssetKey]
    partitions_defs_by_key: Mapping[AssetKey, Optional[PartitionsDefinition]]
    partition_mappings_by_key: Mapping[AssetKey, Optional[Mapping[AssetKey, PartitionMapping]]]
    group_names_by_key: Mapping[AssetKey, Optional[str]]
    freshness_policies_by_key: Mapping[AssetKey, Optional[FreshnessPolicy]]
    required_multi_asset_sets_by_key: Optional[Mapping[AssetKey, AbstractSet[AssetKey]]]

    @staticmethod
    def from_assets(all_assets: Sequence[Union[AssetsDefinition, SourceAsset]]) -> "AssetGraph":
        assets_defs = []
        source_assets = []
        observable_source_asset_keys: AbstractSet[AssetKey] = set()
        partitions_defs_by_key: Dict[AssetKey, Optional[PartitionsDefinition]] = {}
        partition_mappings_by_key: Dict[
            AssetKey, Optional[Mapping[AssetKey, PartitionMapping]]
        ] = {}
        group_names_by_key: Dict[AssetKey, Optional[str]] = {}
        freshness_policies_by_key: Dict[AssetKey, Optional[FreshnessPolicy]] = {}
        required_multi_asset_sets_by_key: Dict[AssetKey, AbstractSet[AssetKey]] = {}

        for asset in all_assets:
            if isinstance(asset, SourceAsset):
                source_assets.append(asset)
                observable_source_asset_keys |= {asset.key}
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
                if len(asset.keys) > 1 and not asset.can_subset:
                    for key in asset.keys:
                        required_multi_asset_sets_by_key[key] = asset.keys

            else:
                check.failed(f"Expected SourceAsset or AssetsDefinition, got {type(asset)}")
        return AssetGraph(
            asset_dep_graph=generate_asset_dep_graph(assets_defs, source_assets),
            source_asset_keys={source_asset.key for source_asset in source_assets},
            observable_source_asset_keys=observable_source_asset_keys,
            partitions_defs_by_key=partitions_defs_by_key,
            partition_mappings_by_key=partition_mappings_by_key,
            group_names_by_key=group_names_by_key,
            freshness_policies_by_key=freshness_policies_by_key,
            required_multi_asset_sets_by_key=required_multi_asset_sets_by_key,
        )

    @staticmethod
    def from_external_assets(external_asset_nodes: Sequence["ExternalAssetNode"]) -> "AssetGraph":
        upstream = {}
        downstream = {}
        source_asset_keys = set()
        observable_source_asset_keys = set()
        partitions_defs_by_key = {}
        partition_mappings_by_key: Dict[AssetKey, Dict[AssetKey, PartitionMapping]] = defaultdict(
            defaultdict
        )
        group_names_by_key = {}
        freshness_policies_by_key = {}

        for node in external_asset_nodes:
            if node.is_source:
                source_asset_keys.add(node.asset_key)
                if node.is_observable:
                    observable_source_asset_keys.add(node.asset_key)
            upstream[node.asset_key] = {dep.upstream_asset_key for dep in node.dependencies}
            downstream[node.asset_key] = {dep.downstream_asset_key for dep in node.depended_by}
            for dep in node.dependencies:
                if dep.partition_mapping is not None:
                    partition_mappings_by_key[node.asset_key][
                        dep.upstream_asset_key
                    ] = dep.partition_mapping
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
            observable_source_asset_keys=observable_source_asset_keys,
            partitions_defs_by_key=partitions_defs_by_key,
            partition_mappings_by_key=partition_mappings_by_key,
            group_names_by_key=group_names_by_key,
            freshness_policies_by_key=freshness_policies_by_key,
            required_multi_asset_sets_by_key=None,
        )

    @property
    def all_asset_keys(self) -> AbstractSet[AssetKey]:
        return self.asset_dep_graph["upstream"].keys()

    def is_observable_source_asset(self, asset_key: AssetKey) -> bool:
        return asset_key in self.observable_source_asset_keys

    def get_partitions_def(self, asset_key: AssetKey) -> Optional[PartitionsDefinition]:
        return self.partitions_defs_by_key.get(asset_key)

    def get_partition_mapping(
        self, asset_key: AssetKey, in_asset_key: AssetKey
    ) -> PartitionMapping:
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
        child_partitions_subset = partition_mapping.get_downstream_partitions_for_partitions(
            parent_partitions_def.empty_subset().with_partition_keys([parent_partition_key]),
            downstream_partitions_def=child_partitions_def,
        )

        return list(child_partitions_subset.get_partition_keys())

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
        parent_partition_key_subset = partition_mapping.get_upstream_partitions_for_partitions(
            cast(PartitionsDefinition, child_partitions_def)
            .empty_subset()
            .with_partition_keys([partition_key])
            if partition_key
            else None,
            upstream_partitions_def=parent_partitions_def,
        )
        return list(parent_partition_key_subset.get_partition_keys())

    def has_non_source_parents(self, asset_key: AssetKey) -> bool:
        """Determines if an asset has any parents which are not source assets"""
        if asset_key in self.source_asset_keys:
            return False
        return bool(self.get_parents(asset_key) - self.source_asset_keys - {asset_key})

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

    def is_non_observable_source_asset(self, asset_key: AssetKey) -> bool:
        return (
            asset_key in self.source_asset_keys
            and asset_key not in self.observable_source_asset_keys
        )

    def has_data_parents(self, asset_key: AssetKey) -> bool:
        if asset_key in self.source_asset_keys:
            return False
        return not all(
            self.is_non_observable_source_asset(parent_key)
            for parent_key in (self.get_parents(asset_key) - {asset_key})
        )

    def get_data_roots(self, asset_key: AssetKey) -> AbstractSet[AssetKey]:
        if not self.has_data_parents(asset_key):
            return {asset_key}
        return {
            key for key in self.upstream_key_iterator(asset_key) if not self.has_data_parents(key)
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

    def get_required_multi_asset_keys(self, asset_key: AssetKey) -> AbstractSet[AssetKey]:
        """For a given asset_key, return the set of asset keys that must be materialized at the same time."""
        if self.required_multi_asset_sets_by_key is None:
            raise DagsterInvariantViolationError(
                "Required neighbor information not set when creating this AssetGraph"
            )
        if asset_key in self.required_multi_asset_sets_by_key:
            return self.required_multi_asset_sets_by_key[asset_key]
        return set()

    def toposort_asset_keys(self) -> Sequence[AbstractSet[AssetKey]]:
        return [
            {key for key in level} for level in toposort.toposort(self.asset_dep_graph["upstream"])
        ]

    def has_self_dependency(self, asset_key: AssetKey) -> bool:
        return asset_key in self.get_parents(asset_key)

    def bfs_filter_asset_partitions(
        self,
        condition_fn: Callable[
            [Iterable[AssetKeyPartitionKey], AbstractSet[AssetKeyPartitionKey]], bool
        ],
        initial_asset_partitions: Iterable[AssetKeyPartitionKey],
    ) -> AbstractSet[AssetKeyPartitionKey]:
        """
        Returns asset partitions within the graph that
        - Are >= initial_asset_partitions
        - Match the condition_fn
        - All of their ancestors >= initial_asset_partitions match the condition_fn
        Visits parents before children.

        When asset partitions are part of the same non-subsettable multi-asset, they're provided all
        at once to the condition_fn.
        """
        all_nodes = set(initial_asset_partitions)

        # invariant: we never consider an asset partition before considering its ancestors
        queue = ToposortedPriorityQueue(self, all_nodes)

        result: Set[AssetKeyPartitionKey] = set()

        while len(queue) > 0:
            candidates_unit = queue.dequeue()

            if condition_fn(candidates_unit, result):
                result.update(candidates_unit)

                for candidate in candidates_unit:
                    for child in self.get_children_partitions(
                        candidate.asset_key, candidate.partition_key
                    ):
                        if child not in all_nodes:
                            queue.enqueue(child)
                            all_nodes.add(child)

        return result

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return self is other


class ToposortedPriorityQueue:
    """Queue that returns parents before their children"""

    @functools.total_ordering
    class QueueItem(NamedTuple):
        level: int
        partition_sort_key: Optional[float]
        multi_asset_partition: Iterable[AssetKeyPartitionKey]

        def __eq__(self, other):
            return self.level == other.level and self.partition_sort_key == other.partition_sort_key

        def __lt__(self, other):
            return self.level < other.level or (
                self.level == other.level
                and self.partition_sort_key is not None
                and self.partition_sort_key < other.partition_sort_key
            )

    def __init__(self, asset_graph: AssetGraph, items: Iterable[AssetKeyPartitionKey]):
        self._asset_graph = asset_graph
        toposorted_asset_keys = asset_graph.toposort_asset_keys()
        self._toposort_level_by_asset_key = {
            asset_key: i
            for i, asset_keys in enumerate(toposorted_asset_keys)
            for asset_key in asset_keys
        }
        self._heap = [self._queue_item(asset_partition) for asset_partition in items]
        heapify(self._heap)

    def enqueue(self, asset_partition: AssetKeyPartitionKey) -> None:
        heappush(self._heap, self._queue_item(asset_partition))

    def dequeue(self) -> Iterable[AssetKeyPartitionKey]:
        return heappop(self._heap).multi_asset_partition

    def _queue_item(self, asset_partition: AssetKeyPartitionKey):
        asset_key = asset_partition.asset_key

        required_multi_asset_keys = self._asset_graph.get_required_multi_asset_keys(asset_key) | {
            asset_key
        }
        level = max(
            self._toposort_level_by_asset_key[required_asset_key]
            for required_asset_key in required_multi_asset_keys
        )
        if self._asset_graph.has_self_dependency(asset_key):
            partitions_def = self._asset_graph.get_partitions_def(asset_key)
            if partitions_def is not None and isinstance(
                partitions_def, TimeWindowPartitionsDefinition
            ):
                partition_sort_key = (
                    cast(TimeWindowPartitionsDefinition, partitions_def)
                    .time_window_for_partition_key(cast(str, asset_partition.partition_key))
                    .start.timestamp()
                )
            else:
                check.failed("Assets with self-dependencies must have time-window partitions")
        else:
            partition_sort_key = None

        return ToposortedPriorityQueue.QueueItem(
            level,
            partition_sort_key,
            [
                AssetKeyPartitionKey(ak, asset_partition.partition_key)
                for ak in required_multi_asset_keys
            ],
        )

    def __len__(self) -> int:
        return len(self._heap)
