from dataclasses import dataclass, replace
from typing import Generic, Optional, Union

from dagster_shared.serdes.serdes import DataclassSerializer, whitelist_for_serdes

import dagster._check as check
from dagster._core.definitions.asset_key import T_EntityKey
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.partition import (
    AllPartitionsSubset,
    PartitionsDefinition,
    PartitionsSubset,
)
from dagster._core.definitions.time_window_partitions import TimeWindowPartitionsSubset

EntitySubsetValue = Union[bool, PartitionsSubset]


class EntitySubsetSerializer(DataclassSerializer):
    """Ensures that the inner PartitionsSubset is converted to a serializable form if necessary."""

    def get_storage_name(self) -> str:
        # backcompat
        return "AssetSubset"

    def before_pack(self, value: "SerializableEntitySubset") -> "SerializableEntitySubset":  # pyright: ignore[reportIncompatibleMethodOverride]
        if value.is_partitioned:
            return replace(value, value=value.subset_value.to_serializable_subset())
        return value


@whitelist_for_serdes(
    serializer=EntitySubsetSerializer,
    storage_field_names={"key": "asset_key"},
    old_storage_names={"AssetSubset"},
)
@dataclass(frozen=True)
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
            if isinstance(self.value, (TimeWindowPartitionsSubset, AllPartitionsSubset)):
                return self.value.partitions_def == partitions_def
            else:
                return partitions_def is not None
        else:
            return partitions_def is None

    def _check_incoming_value_is_compatible(self, value: EntitySubsetValue) -> None:
        incoming_is_partitioned = not isinstance(value, bool)
        if self.is_partitioned and not incoming_is_partitioned:
            raise ValueError(
                f"Cannot add {value} to subset. The types are incompatible. EntitySubset is partitioned"
            )
        if not self.is_partitioned and incoming_is_partitioned:
            raise ValueError(
                f"Cannot add {value} to subset. The types are incompatible. EntitySubset is not partitioned"
            )

    def add(self, value: EntitySubsetValue) -> "SerializableEntitySubset":
        self._check_incoming_value_is_compatible(value)

        if self.is_partitioned:
            return SerializableEntitySubset(
                self.key, self.subset_value | check.inst(value, PartitionsSubset)
            )
        else:
            return SerializableEntitySubset(self.key, True)

    def remove(self, value: EntitySubsetValue) -> "SerializableEntitySubset":
        self._check_incoming_value_is_compatible(value)
        if self.is_partitioned:
            return SerializableEntitySubset(
                self.key, self.subset_value - check.inst(value, PartitionsSubset)
            )
        else:
            return SerializableEntitySubset(self.key, False)

    def __contains__(self, item: AssetKeyPartitionKey) -> bool:
        if not self.is_partitioned:
            return item.asset_key == self.key and item.partition_key is None and self.bool_value
        else:
            return item.asset_key == self.key and item.partition_key in self.subset_value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}<{self.key}>({self.value})"
