from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence, Set
from functools import cached_property
from typing import TYPE_CHECKING, Generic, Union, cast

from dagster._core.asset_graph_view.entity_subset import EntitySubset
from dagster._core.definitions.asset_key import AssetKey, T_EntityKey
from dagster._core.definitions.assets.graph.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.assets.graph.base_asset_graph import BaseAssetGraph
from dagster._core.definitions.events import AssetKeyPartitionKey

if TYPE_CHECKING:
    from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView


class AssetGraphSubsetView(Generic[T_EntityKey]):
    def __init__(
        self,
        asset_graph_view: "AssetGraphView",
        subsets: Sequence[EntitySubset[T_EntityKey]],
    ):
        self._asset_graph_view = asset_graph_view
        self._subsets = subsets

    @property
    def keys(self) -> Set[T_EntityKey]:
        return {subset.key for subset in self.subsets}

    @property
    def subsets(self) -> Sequence[EntitySubset[T_EntityKey]]:
        return self._subsets

    @property
    def asset_graph(self) -> BaseAssetGraph:
        return self._asset_graph_view.asset_graph

    @cached_property
    def subsets_by_key(self) -> Mapping[T_EntityKey, EntitySubset[T_EntityKey]]:
        return {subset.key: subset for subset in self.subsets}

    @property
    def is_empty(self) -> bool:
        return all(subset.is_empty for subset in self.subsets)

    @property
    def size(self) -> int:
        return sum(subset.size for subset in self.subsets)

    @staticmethod
    def empty(asset_graph_view: "AssetGraphView") -> "AssetGraphSubsetView[T_EntityKey]":
        return AssetGraphSubsetView(asset_graph_view=asset_graph_view, subsets=[])

    @staticmethod
    def from_serializable_subset(
        asset_graph_view: "AssetGraphView",
        serializable_subset: AssetGraphSubset,
    ) -> "AssetGraphSubsetView[AssetKey]":
        return AssetGraphSubsetView(
            asset_graph_view=asset_graph_view,
            subsets=list(asset_graph_view.iterate_asset_subsets(serializable_subset)),
        )

    @staticmethod
    def from_asset_partitions(
        asset_graph_view: "AssetGraphView",
        asset_partitions: Iterable[AssetKeyPartitionKey],
    ) -> "AssetGraphSubsetView[AssetKey]":
        # Group partition keys by asset key
        asset_to_partitions = defaultdict(set)
        for asset_partition in asset_partitions:
            asset_to_partitions[asset_partition.asset_key].add(asset_partition)

        # Create subsets for each asset
        subsets = [
            asset_graph_view.get_asset_subset_from_asset_partitions(asset_key, partition_keys)
            for asset_key, partition_keys in asset_to_partitions.items()
        ]

        return AssetGraphSubsetView(asset_graph_view=asset_graph_view, subsets=subsets)

    def get(self, key: T_EntityKey) -> EntitySubset[T_EntityKey]:
        if key not in self.subsets_by_key:
            return self._asset_graph_view.get_empty_subset(key=key)
        return self.subsets_by_key[key]

    def _coerce_to_subset_view(
        self, other: Union["AssetGraphSubsetView[T_EntityKey]", EntitySubset[T_EntityKey]]
    ) -> "AssetGraphSubsetView[T_EntityKey]":
        if isinstance(other, AssetGraphSubsetView):
            return other
        return AssetGraphSubsetView(asset_graph_view=self._asset_graph_view, subsets=[other])

    def compute_difference(
        self, other: Union["AssetGraphSubsetView[T_EntityKey]", EntitySubset[T_EntityKey]]
    ) -> "AssetGraphSubsetView[T_EntityKey]":
        other = self._coerce_to_subset_view(other)
        subsets = []
        for subset in self.subsets:
            subsets.append(subset.compute_difference(other.get(subset.key)))
        return AssetGraphSubsetView(asset_graph_view=self._asset_graph_view, subsets=subsets)

    def compute_intersection(
        self, other: Union["AssetGraphSubsetView[T_EntityKey]", EntitySubset[T_EntityKey]]
    ) -> "AssetGraphSubsetView[T_EntityKey]":
        other = self._coerce_to_subset_view(other)
        subsets = []
        for subset in self.subsets:
            subsets.append(subset.compute_intersection(other.get(subset.key)))
        return AssetGraphSubsetView(asset_graph_view=self._asset_graph_view, subsets=subsets)

    def compute_union(
        self, other: Union["AssetGraphSubsetView[T_EntityKey]", EntitySubset[T_EntityKey]]
    ) -> "AssetGraphSubsetView[T_EntityKey]":
        other = self._coerce_to_subset_view(other)
        subsets = []
        for subset in self.subsets:
            subsets.append(subset.compute_union(other.get(subset.key)))
        for subset in other.subsets:
            if subset.key not in self.subsets_by_key:
                subsets.append(subset)
        return AssetGraphSubsetView(asset_graph_view=self._asset_graph_view, subsets=subsets)

    def compute_downstream_subset(self) -> "AssetGraphSubsetView[T_EntityKey]":
        return self._asset_graph_view.compute_downstream_asset_graph_subset_view(self)

    def to_asset_graph_subset(self) -> AssetGraphSubset:
        asset_subsets = [
            cast("EntitySubset[AssetKey]", subset)
            for subset in self.subsets
            if isinstance(subset.key, AssetKey)
        ]
        return AssetGraphSubset.from_entity_subsets(asset_subsets)

    def pprint(self) -> str:
        if self.is_empty:
            return "AssetGraphSubsetView([])"
        else:
            subset_str = "\n".join([f"    {subset}" for subset in self.subsets])
            return f"AssetGraphSubsetView(\n{subset_str}\n)"

    def __str__(self) -> str:
        return self.pprint()
