import operator
from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Any, Callable, Generic, Optional, Union

from dagster_shared.serdes.serdes import DataclassSerializer, whitelist_for_serdes
from typing_extensions import Self

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

CoercibleToAssetEntitySubsetValue = Union[str, Sequence[str], PartitionsSubset, None]


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

    @classmethod
    def from_coercible_value(
        cls,
        key: T_EntityKey,
        value: CoercibleToAssetEntitySubsetValue,
        partitions_def: Optional[PartitionsDefinition],
    ) -> "SerializableEntitySubset":
        """Creates a new SerializableEntitySubset, handling coercion of a CoercibleToAssetEntitySubsetValue
        to an EntitySubsetValue.
        """
        if value is None:
            check.invariant(
                partitions_def is None,
                "Cannot create a SerializableEntitySubset with value=None and non-None partitions_def",
            )
            return cls(key=key, value=True)
        if isinstance(value, str):
            partitions_subset = check.not_none(partitions_def).subset_with_partition_keys([value])
        elif isinstance(value, PartitionsSubset):
            check.inst_param(value, "value", PartitionsSubset)
            partitions_subset = value
        else:
            check.list_param(value, "value", of_type=str)
            partitions_subset = check.not_none(partitions_def).subset_with_partition_keys(value)
        return cls(key=key, value=partitions_subset)

    @classmethod
    def try_from_coercible_value(
        cls,
        key: T_EntityKey,
        value: CoercibleToAssetEntitySubsetValue,
        partitions_def: Optional[PartitionsDefinition],
    ) -> Optional["SerializableEntitySubset"]:
        """Attempts to create a new SerializableEntitySubset, handling coercion of a CoercibleToAssetEntitySubsetValue
        and partitions definition to an EntitySubsetValue. Returns None if the coercion fails.
        """
        try:
            return cls.from_coercible_value(key, value, partitions_def)
        except check.CheckError:
            return None

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

    def _oper(self, other: Self, oper: Callable[..., Any]) -> Self:
        check.invariant(self.key == other.key, "Keys must match for operation")
        value = oper(self.value, other.value)
        return self.__class__(key=self.key, value=value)

    def compute_difference(self, other: Self) -> Self:
        if isinstance(self.value, bool):
            value = self.bool_value and not other.bool_value
            return self.__class__(key=self.key, value=value)
        else:
            return self._oper(other, operator.sub)

    def compute_union(self, other: Self) -> Self:
        return self._oper(other, operator.or_)

    def compute_intersection(self, other: Self) -> Self:
        return self._oper(other, operator.and_)

    def __contains__(self, item: AssetKeyPartitionKey) -> bool:
        if not self.is_partitioned:
            return item.asset_key == self.key and item.partition_key is None and self.bool_value
        else:
            return item.asset_key == self.key and item.partition_key in self.subset_value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}<{self.key}>({self.value})"
