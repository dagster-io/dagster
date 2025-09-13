import operator
from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Any, Callable, Generic, Optional, Union

from dagster_shared.serdes.serdes import DataclassSerializer, whitelist_for_serdes
from typing_extensions import Self

import dagster._check as check
from dagster._core.definitions.asset_key import T_EntityKey
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.definitions.partitions.definition import PartitionsDefinition
from dagster._core.definitions.partitions.snap.snap import PartitionsSnap
from dagster._core.definitions.partitions.subset import (
    AllPartitionsSubset,
    DefaultPartitionsSubset,
    PartitionsSubset,
    TimeWindowPartitionsSubset,
)
from dagster._core.definitions.partitions.subset.key_ranges import KeyRangesPartitionsSubset

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
            partitions_def = check.not_none(partitions_def)
            if partitions_def.partitions_subset_class is not DefaultPartitionsSubset:
                # DefaultPartitionsSubset just adds partition keys to a set, but other subsets
                # may require partition keys be part of the partition, so validate the key
                with partition_loading_context() as ctx:
                    partitions_def.validate_partition_key(value, context=ctx)
            partitions_subset = partitions_def.subset_with_partition_keys([value])
        elif isinstance(value, PartitionsSubset):
            if partitions_def is not None:
                check.inst_param(
                    value,
                    "value",
                    partitions_def.partitions_subset_class,
                )
            partitions_subset = value
        else:
            check.list_param(value, "value", of_type=str)
            partitions_def = check.not_none(partitions_def)
            partitions_subset = partitions_def.subset_with_partition_keys(value)
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
        except:
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
            # for KeyRangesPartitionsSubset, we have the PartitionsSnap, so we can use that
            elif isinstance(self.value, KeyRangesPartitionsSubset):
                if (
                    partitions_def is None
                    or PartitionsSnap.from_def(partitions_def) != self.value.partitions_snap
                ):
                    return False
                # all ranges must be valid
                return all(
                    partitions_def.has_partition_key(r.start)
                    and partitions_def.has_partition_key(r.end)
                    for r in self.value.key_ranges
                )
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
