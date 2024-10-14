from typing import Generic, Optional, Union

import dagster._check as check
from dagster._core.definitions.asset_key import T_EntityKey
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.partition import (
    AllPartitionsSubset,
    PartitionsDefinition,
    PartitionsSubset,
)
from dagster._core.definitions.time_window_partitions import BaseTimeWindowPartitionsSubset
from dagster._record import record, replace
from dagster._serdes.serdes import NamedTupleSerializer, whitelist_for_serdes

EntitySubsetValue = Union[bool, PartitionsSubset]


class EntitySubsetSerializer(NamedTupleSerializer):
    """Ensures that the inner PartitionsSubset is converted to a serializable form if necessary."""

    def get_storage_name(self) -> str:
        # backcompat
        return "AssetSubset"

    def before_pack(self, value: "SerializableEntitySubset") -> "SerializableEntitySubset":
        if value.is_partitioned:
            return replace(value, value=value.subset_value.to_serializable_subset())
        return value


@whitelist_for_serdes(
    serializer=EntitySubsetSerializer,
    storage_field_names={"key": "asset_key"},
    old_storage_names={"AssetSubset"},
)
@record(checked=False)
class SerializableEntitySubset(Generic[T_EntityKey]):
    """Represents a serializable subset of a given EntityKey."""

    key: T_EntityKey
    value: EntitySubsetValue

    @property
    def is_partitioned(self) -> bool:
        return not isinstance(self.value, bool)

    @property
    def bool_value(self) -> bool:
        return check.inst(self.value, bool)

    @property
    def subset_value(self) -> PartitionsSubset:
        return check.inst(self.value, PartitionsSubset)

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

    def __contains__(self, item: AssetKeyPartitionKey) -> bool:
        if not self.is_partitioned:
            return item.asset_key == self.key and item.partition_key is None and self.bool_value
        else:
            return item.asset_key == self.key and item.partition_key in self.subset_value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}<{self.key}>({self.value})"
