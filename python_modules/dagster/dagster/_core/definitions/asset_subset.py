from dataclasses import dataclass, replace
from typing import AbstractSet, Generic, Optional, TypeVar, Union, cast

import dagster._check as check
from dagster._core.definitions.asset_key import AssetGraphEntityKey
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.partition import (
    AllPartitionsSubset,
    PartitionsDefinition,
    PartitionsSubset,
)
from dagster._core.definitions.time_window_partitions import BaseTimeWindowPartitionsSubset
from dagster._serdes.serdes import DataclassSerializer, whitelist_for_serdes

T = TypeVar("T", bound=AssetGraphEntityKey)
AssetGraphEntitySubsetValue = Union[bool, PartitionsSubset]


@dataclass(frozen=True)
class AssetGraphEntitySubset(Generic[T]):
    """Generic base class for representing a subset of an AssetGraphEntity."""

    key: T
    value: AssetGraphEntitySubsetValue

    @property
    def is_partitioned(self) -> bool:
        return not isinstance(self.value, bool)

    @property
    def bool_value(self) -> bool:
        check.invariant(isinstance(self.value, bool))
        return cast(bool, self.value)

    @property
    def subset_value(self) -> PartitionsSubset:
        check.invariant(isinstance(self.value, PartitionsSubset))
        return cast(PartitionsSubset, self.value)

    @property
    def size(self) -> int:
        if not self.is_partitioned:
            return int(self.bool_value)
        else:
            return len(self.subset_value)

    @property
    def is_empty(self) -> bool:
        if self.is_partitioned:
            return self.subset_value.is_empty
        else:
            return not self.bool_value

    def is_compatible_with_partitions_def(
        self, partitions_def: Optional[PartitionsDefinition]
    ) -> bool:
        if self.is_partitioned:
            # for some PartitionSubset types, we have access to the underlying partitions
            # definitions, so we can ensure those are identical
            if isinstance(self.value, (BaseTimeWindowPartitionsSubset, AllPartitionsSubset)):
                return self.value.partitions_def == partitions_def
            else:
                return partitions_def is not None
        else:
            return partitions_def is None


class AssetSubsetSerializer(DataclassSerializer):
    """Ensures that the inner PartitionsSubset is converted to a serializable form if necessary."""

    def get_storage_name(self) -> str:
        # override this method so all ValidAssetSubsets are serialzied as AssetSubsets
        return "AssetSubset"

    def before_pack(self, value: "AssetSubset") -> "AssetSubset":
        if value.is_partitioned:
            return replace(value, value=value.subset_value.to_serializable_subset())
        return value


@whitelist_for_serdes(serializer=AssetSubsetSerializer, storage_field_names={"key": "asset_key"})
@dataclass(frozen=True)
class AssetSubset(AssetGraphEntitySubset[AssetKey]):
    """Represents a set of AssetKeyPartitionKeys for a given AssetKey. For partitioned assets, this
    class uses a PartitionsSubset to represent the set of partitions, enabling lazy evaluation of the
    underlying partition keys. For unpartitioned assets, this class uses a bool to represent whether
    the asset is present or not.
    """

    key: AssetKey
    value: AssetGraphEntitySubsetValue

    @property
    def asset_key(self) -> AssetKey:
        return self.key

    @property
    def asset_partitions(self) -> AbstractSet[AssetKeyPartitionKey]:
        if not self.is_partitioned:
            return {AssetKeyPartitionKey(self.asset_key)} if self.bool_value else set()
        else:
            return {
                AssetKeyPartitionKey(self.asset_key, partition_key)
                for partition_key in self.subset_value.get_partition_keys()
            }

    def __contains__(self, item: AssetKeyPartitionKey) -> bool:
        if not self.is_partitioned:
            return (
                item.asset_key == self.asset_key and item.partition_key is None and self.bool_value
            )
        else:
            return item.asset_key == self.asset_key and item.partition_key in self.subset_value
