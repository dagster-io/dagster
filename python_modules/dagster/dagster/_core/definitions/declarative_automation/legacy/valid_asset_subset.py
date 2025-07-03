import operator
from dataclasses import replace
from typing import AbstractSet, Any, Callable, Optional  # noqa: UP035

from dagster_shared.serdes import whitelist_for_serdes

from dagster._core.asset_graph_view.serializable_entity_subset import (
    EntitySubsetSerializer,
    SerializableEntitySubset,
)
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.definitions.partitions.definition import PartitionsDefinition
from dagster._core.definitions.partitions.subset import (
    AllPartitionsSubset,
    TimeWindowPartitionsSubset,
)


@whitelist_for_serdes(serializer=EntitySubsetSerializer, storage_field_names={"key": "asset_key"})
class ValidAssetSubset(SerializableEntitySubset[AssetKey]):
    """Legacy construct used for doing operations over EntitySubsets that are known to be valid. This
    functionality is subsumed by EntitySubset.
    """

    def inverse(self, partitions_def: Optional[PartitionsDefinition]) -> "ValidAssetSubset":
        """Returns the EntitySubset containing all asset partitions which are not in this EntitySubset."""
        if partitions_def is None:
            return replace(self, value=not self.bool_value)
        else:
            value = partitions_def.subset_with_partition_keys(
                self.subset_value.get_partition_keys_not_in_subset(partitions_def)
            )
            return replace(self, value=value)

    def _oper(self, other: "ValidAssetSubset", oper: Callable[..., Any]) -> "ValidAssetSubset":
        value = oper(self.value, other.value)
        return replace(self, value=value)

    def __sub__(self, other: SerializableEntitySubset) -> "ValidAssetSubset":
        """Returns an EntitySubset representing self.asset_partitions - other.asset_partitions."""
        valid_other = self.get_valid(other)
        if not self.is_partitioned:
            return replace(self, value=self.bool_value and not valid_other.bool_value)
        return self._oper(valid_other, operator.sub)

    def __and__(self, other: SerializableEntitySubset) -> "ValidAssetSubset":
        """Returns an EntitySubset representing self.asset_partitions & other.asset_partitions."""
        return self._oper(self.get_valid(other), operator.and_)

    def __or__(self, other: SerializableEntitySubset) -> "ValidAssetSubset":
        """Returns an EntitySubset representing self.asset_partitions | other.asset_partitions."""
        return self._oper(self.get_valid(other), operator.or_)

    @staticmethod
    def coerce_from_subset(
        subset: SerializableEntitySubset, partitions_def: Optional[PartitionsDefinition]
    ) -> "ValidAssetSubset":
        """Converts an EntitySubset to a ValidAssetSubset by returning a copy of this EntitySubset
        if it is compatible with the given PartitionsDefinition, otherwise returns an empty subset.
        """
        if subset.is_compatible_with_partitions_def(partitions_def):
            return ValidAssetSubset(key=subset.key, value=subset.value)
        else:
            return ValidAssetSubset.empty(subset.key, partitions_def)

    def _is_compatible_with_subset(self, other: "SerializableEntitySubset") -> bool:
        if isinstance(other.value, (TimeWindowPartitionsSubset, AllPartitionsSubset)):
            return self.is_compatible_with_partitions_def(other.value.partitions_def)
        else:
            return self.is_partitioned == other.is_partitioned

    def get_valid(self, other: SerializableEntitySubset) -> "ValidAssetSubset":
        """Creates a ValidAssetSubset from the given EntitySubset by returning a replace of the given
        EntitySubset if it is compatible with this EntitySubset, otherwise returns an empty subset.
        """
        if isinstance(other, ValidAssetSubset):
            return other
        elif self._is_compatible_with_subset(other):
            return ValidAssetSubset(key=other.key, value=other.value)
        else:
            return replace(
                self,
                # unfortunately, this is the best way to get an empty partitions subset of an unknown
                # type if you don't have access to the partitions definition
                value=(self.subset_value - self.subset_value) if self.is_partitioned else False,
            )

    @staticmethod
    def all(
        asset_key: AssetKey, partitions_def: Optional[PartitionsDefinition]
    ) -> "ValidAssetSubset":
        if partitions_def is None:
            return ValidAssetSubset(key=asset_key, value=True)
        else:
            with partition_loading_context() as ctx:
                return ValidAssetSubset(
                    key=asset_key, value=AllPartitionsSubset(partitions_def, ctx)
                )

    @staticmethod
    def empty(
        asset_key: AssetKey, partitions_def: Optional[PartitionsDefinition]
    ) -> "ValidAssetSubset":
        if partitions_def is None:
            return ValidAssetSubset(key=asset_key, value=False)
        else:
            return ValidAssetSubset(key=asset_key, value=partitions_def.empty_subset())

    @staticmethod
    def from_asset_partitions_set(
        asset_key: AssetKey,
        partitions_def: Optional[PartitionsDefinition],
        asset_partitions_set: AbstractSet[AssetKeyPartitionKey],
    ) -> "ValidAssetSubset":
        return (
            ValidAssetSubset.from_partition_keys(
                asset_key=asset_key,
                partitions_def=partitions_def,
                partition_keys={
                    ap.partition_key for ap in asset_partitions_set if ap.partition_key is not None
                },
            )
            if partitions_def
            else ValidAssetSubset(key=asset_key, value=bool(asset_partitions_set))
        )

    @staticmethod
    def from_partition_keys(
        asset_key: AssetKey,
        partitions_def: PartitionsDefinition,
        partition_keys: AbstractSet[str],
    ) -> "ValidAssetSubset":
        return ValidAssetSubset(
            key=asset_key, value=partitions_def.subset_with_partition_keys(partition_keys)
        )

    @property
    def asset_partitions(self) -> AbstractSet[AssetKeyPartitionKey]:
        if not self.is_partitioned:
            return {AssetKeyPartitionKey(self.key)} if self.bool_value else set()
        else:
            return {
                AssetKeyPartitionKey(self.key, partition_key)
                for partition_key in self.subset_value.get_partition_keys()
            }
