from collections import defaultdict
from typing import AbstractSet, Any, Dict, Iterable, Mapping, Optional, Set, Union, cast

from dagster import _check as check
from dagster._core.definitions.partition import PartitionsDefinition, PartitionsSubset
from dagster._core.errors import DagsterDefinitionChangedDeserializationError

from .asset_graph import AssetGraph
from .events import AssetKey, AssetKeyPartitionKey


class AssetGraphSubset:
    def __init__(
        self,
        asset_graph: AssetGraph,
        partitions_subsets_by_asset_key: Optional[Mapping[AssetKey, PartitionsSubset]] = None,
        non_partitioned_asset_keys: Optional[AbstractSet[AssetKey]] = None,
    ):
        self._asset_graph = asset_graph
        self._partitions_subsets_by_asset_key = partitions_subsets_by_asset_key or {}
        self._non_partitioned_asset_keys = non_partitioned_asset_keys or set()

    @property
    def asset_graph(self):
        return self._asset_graph

    @property
    def partitions_subsets_by_asset_key(self):
        return self._partitions_subsets_by_asset_key

    @property
    def non_partitioned_asset_keys(self):
        return self._non_partitioned_asset_keys

    @property
    def asset_keys(self) -> Iterable[AssetKey]:
        return self.partitions_subsets_by_asset_key.keys() | self._non_partitioned_asset_keys

    @property
    def num_partitions_and_non_partitioned_assets(self):
        return len(self._non_partitioned_asset_keys) + sum(
            len(subset) for subset in self._partitions_subsets_by_asset_key.values()
        )

    def get_partitions_subset(self, asset_key: AssetKey) -> PartitionsSubset:
        partitions_def = self.asset_graph.get_partitions_def(asset_key)
        if partitions_def is None:
            check.failed("Can only call get_partitions_subset on a partitioned asset")

        return self.partitions_subsets_by_asset_key.get(asset_key, partitions_def.empty_subset())

    def iterate_asset_partitions(self) -> Iterable[AssetKeyPartitionKey]:
        for asset_key, partitions_subset in self.partitions_subsets_by_asset_key.items():
            for partition_key in partitions_subset.get_partition_keys():
                yield AssetKeyPartitionKey(asset_key, partition_key)

        for asset_key in self._non_partitioned_asset_keys:
            yield AssetKeyPartitionKey(asset_key, None)

    def __contains__(self, asset_partition: AssetKeyPartitionKey) -> bool:
        if asset_partition.partition_key is None:
            return asset_partition.asset_key in self._non_partitioned_asset_keys
        else:
            partitions_subset = self.partitions_subsets_by_asset_key.get(asset_partition.asset_key)
            return (
                partitions_subset is not None and asset_partition.partition_key in partitions_subset
            )

    def to_storage_dict(self) -> Mapping[str, object]:
        return {
            "partitions_subsets_by_asset_key": {
                key.to_user_string(): value.serialize()
                for key, value in self.partitions_subsets_by_asset_key.items()
            },
            "non_partitioned_asset_keys": [
                key.to_user_string() for key in self._non_partitioned_asset_keys
            ],
        }

    def __or__(
        self, other: Union["AssetGraphSubset", AbstractSet[AssetKeyPartitionKey]]
    ) -> "AssetGraphSubset":
        result_partition_subsets_by_asset_key = {**self.partitions_subsets_by_asset_key}
        result_non_partitioned_asset_keys = set(self._non_partitioned_asset_keys)

        if not isinstance(other, AssetGraphSubset):
            other = AssetGraphSubset.from_asset_partition_set(other, self.asset_graph)

        for asset_key in other.asset_keys:
            if asset_key in other.non_partitioned_asset_keys:
                check.invariant(asset_key not in self.partitions_subsets_by_asset_key)
                result_non_partitioned_asset_keys.add(asset_key)
            else:
                subset = self.get_partitions_subset(asset_key)
                check.invariant(asset_key not in self.non_partitioned_asset_keys)
                result_partition_subsets_by_asset_key[asset_key] = subset.with_partition_keys(
                    other.get_partitions_subset(asset_key).get_partition_keys()
                )

        return AssetGraphSubset(
            self.asset_graph,
            result_partition_subsets_by_asset_key,
            result_non_partitioned_asset_keys,
        )

    def filter_asset_keys(self, asset_keys: AbstractSet[AssetKey]) -> "AssetGraphSubset":
        return AssetGraphSubset(
            self.asset_graph,
            {
                asset_key: subset
                for asset_key, subset in self.partitions_subsets_by_asset_key.items()
                if asset_key in asset_keys
            },
            self._non_partitioned_asset_keys & asset_keys,
        )

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, AssetGraphSubset)
            and self.asset_graph == other.asset_graph
            and self.partitions_subsets_by_asset_key == other.partitions_subsets_by_asset_key
        )

    def __repr__(self) -> str:
        return (
            "AssetGraphSubset("
            f"non_partitioned_asset_keys={self.non_partitioned_asset_keys}, "
            f"partitions_subset_by_asset_key={self.partitions_subsets_by_asset_key}"
            ")"
        )

    @classmethod
    def from_asset_partition_set(
        cls, asset_partitions_set: AbstractSet[AssetKeyPartitionKey], asset_graph: AssetGraph
    ) -> "AssetGraphSubset":
        partitions_by_asset_key = defaultdict(set)
        non_partitioned_asset_keys = set()
        for asset_key, partition_key in asset_partitions_set:
            if partition_key is not None:
                partitions_by_asset_key[asset_key].add(partition_key)
            else:
                non_partitioned_asset_keys.add(asset_key)

        return AssetGraphSubset(
            partitions_subsets_by_asset_key={
                asset_key: cast(PartitionsDefinition, asset_graph.get_partitions_def(asset_key))
                .empty_subset()
                .with_partition_keys(partition_keys)
                for asset_key, partition_keys in partitions_by_asset_key.items()
            },
            non_partitioned_asset_keys=non_partitioned_asset_keys,
            asset_graph=asset_graph,
        )

    @classmethod
    def from_storage_dict(
        cls, serialized_dict: Mapping[str, Any], asset_graph: AssetGraph
    ) -> "AssetGraphSubset":
        partitions_subsets_by_asset_key: Dict[AssetKey, PartitionsSubset] = {}
        for key, value in serialized_dict["partitions_subsets_by_asset_key"].items():
            asset_key = AssetKey.from_user_string(key)
            partitions_def = asset_graph.get_partitions_def(asset_key)
            if partitions_def is None:
                raise DagsterDefinitionChangedDeserializationError(
                    f"Asset {key} had a PartitionsDefinition at storage-time, but no longer does"
                )

            partitions_subsets_by_asset_key[asset_key] = partitions_def.deserialize_subset(value)

        non_partitioned_asset_keys = {
            AssetKey.from_user_string(key) for key in serialized_dict["non_partitioned_asset_keys"]
        }

        return AssetGraphSubset(
            asset_graph, partitions_subsets_by_asset_key, non_partitioned_asset_keys
        )

    @classmethod
    def all(cls, asset_graph: AssetGraph) -> "AssetGraphSubset":
        partitions_subsets_by_asset_key: Dict[AssetKey, PartitionsSubset] = {}
        non_partitioned_asset_keys: Set[AssetKey] = set()

        for asset_key in asset_graph.all_asset_keys:
            partitions_def = asset_graph.get_partitions_def(asset_key)
            if partitions_def:
                partitions_subsets_by_asset_key[
                    asset_key
                ] = partitions_def.empty_subset().with_partition_keys(
                    partitions_def.get_partition_keys()
                )
            else:
                non_partitioned_asset_keys.add(asset_key)

        return AssetGraphSubset(
            asset_graph, partitions_subsets_by_asset_key, non_partitioned_asset_keys
        )
