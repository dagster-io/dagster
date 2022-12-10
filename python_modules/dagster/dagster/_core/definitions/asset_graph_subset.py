from collections import defaultdict
from typing import AbstractSet, Dict, Iterable, Mapping, cast

from dagster._core.definitions.partition import PartitionsDefinition, PartitionsSubset

from .asset_graph import AssetGraph
from .events import AssetKey, AssetKeyPartitionKey


class AssetGraphSubset:
    def __init__(
        self,
        partitions_subsets_by_asset_key: Mapping[AssetKey, PartitionsSubset],
        asset_graph: AssetGraph,
    ):
        self._partitions_subsets_by_asset_key = partitions_subsets_by_asset_key
        self._asset_graph = asset_graph

    @property
    def asset_graph(self):
        return self._asset_graph

    @property
    def partitions_subsets_by_asset_key(self):
        return self._partitions_subsets_by_asset_key

    @property
    def asset_keys(self) -> Iterable[AssetKey]:
        return self.partitions_subsets_by_asset_key.keys()

    def get_partitions_subset(self, asset_key: AssetKey) -> PartitionsSubset:
        partitions_def = cast(PartitionsDefinition, self.asset_graph.get_partitions_def(asset_key))
        return self.partitions_subsets_by_asset_key.get(asset_key, partitions_def.empty_subset())

    def __contains__(self, asset_partition: AssetKeyPartitionKey) -> bool:
        partitions_subset = self.partitions_subsets_by_asset_key.get(asset_partition.asset_key)
        return partitions_subset is not None and asset_partition.partition_key in partitions_subset

    def to_storage_dict(self) -> Mapping[str, str]:
        return {
            key.to_user_string(): value.serialize()
            for key, value in self.partitions_subsets_by_asset_key.items()
        }

    def __or__(self, other: Mapping[AssetKey, AbstractSet[str]]) -> "AssetGraphSubset":
        result_partition_subsets_by_asset_key: Dict[AssetKey, PartitionsSubset] = {}
        for asset_key in self.partitions_subsets_by_asset_key.keys() | other.keys():
            subset = self.get_partitions_subset(asset_key)
            result_partition_subsets_by_asset_key[asset_key] = subset.with_partition_keys(
                other.get(asset_key, [])
            )

        return AssetGraphSubset(result_partition_subsets_by_asset_key, self.asset_graph)

    @classmethod
    def from_asset_partition_set(
        cls, asset_partitions_set: AbstractSet[AssetKeyPartitionKey], asset_graph: AssetGraph
    ) -> "AssetGraphSubset":
        partitions_by_asset_key = defaultdict(set)
        for asset_key, partition_key in asset_partitions_set:
            partitions_by_asset_key[asset_key].add(cast(str, partition_key))

        return AssetGraphSubset(
            {
                asset_key: cast(PartitionsDefinition, asset_graph.get_partitions_def(asset_key))
                .empty_subset()
                .with_partition_keys(partition_keys)
                for asset_key, partition_keys in partitions_by_asset_key.items()
            },
            asset_graph,
        )

    @classmethod
    def from_storage_dict(
        cls, serialized_dict: Mapping[str, str], asset_graph: AssetGraph
    ) -> "AssetGraphSubset":
        result: Dict[AssetKey, PartitionsSubset] = {}
        for key, value in serialized_dict.items():
            asset_key = AssetKey.from_user_string(key)
            partitions_def = cast(PartitionsDefinition, asset_graph.get_partitions_def(asset_key))
            result[asset_key] = partitions_def.deserialize_subset(value)

        return AssetGraphSubset(result, asset_graph)
