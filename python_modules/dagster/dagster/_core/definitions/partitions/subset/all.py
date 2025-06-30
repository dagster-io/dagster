from collections.abc import Iterable, Sequence
from datetime import datetime
from typing import NamedTuple, Optional

import dagster._check as check
from dagster._core.definitions.partitions.definition.partitions_definition import (
    PartitionsDefinition,
)
from dagster._core.definitions.partitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.partitions.subset.partitions_subset import PartitionsSubset
from dagster._core.instance import DynamicPartitionsStore


class AllPartitionsSubset(
    NamedTuple(
        "_AllPartitionsSubset",
        [
            ("partitions_def", PartitionsDefinition),
            ("dynamic_partitions_store", "DynamicPartitionsStore"),
            ("current_time", datetime),
        ],
    ),
    PartitionsSubset,
):
    """This is an in-memory (i.e. not serializable) convenience class that represents all partitions
    of a given PartitionsDefinition, allowing set operations to be taken without having to load
    all partition keys immediately.
    """

    def __new__(
        cls,
        partitions_def: PartitionsDefinition,
        dynamic_partitions_store: DynamicPartitionsStore,
        current_time: datetime,
    ):
        return super().__new__(
            cls,
            partitions_def=partitions_def,
            dynamic_partitions_store=dynamic_partitions_store,
            current_time=current_time,
        )

    @property
    def is_empty(self) -> bool:
        return False

    def get_partition_keys(self, current_time: Optional[datetime] = None) -> Sequence[str]:
        check.param_invariant(current_time is None, "current_time")
        return self.partitions_def.get_partition_keys(
            self.current_time, self.dynamic_partitions_store
        )

    def get_partition_keys_not_in_subset(
        self,
        partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> Iterable[str]:
        return set()

    def get_partition_key_ranges(
        self,
        partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> Sequence[PartitionKeyRange]:
        check.param_invariant(current_time is None, "current_time")
        check.param_invariant(dynamic_partitions_store is None, "dynamic_partitions_store")
        first_key = partitions_def.get_first_partition_key(
            self.current_time, self.dynamic_partitions_store
        )
        last_key = partitions_def.get_last_partition_key(
            self.current_time, self.dynamic_partitions_store
        )
        if first_key and last_key:
            return [PartitionKeyRange(first_key, last_key)]
        return []

    def with_partition_keys(self, partition_keys: Iterable[str]) -> "AllPartitionsSubset":
        return self

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, AllPartitionsSubset) and other.partitions_def == self.partitions_def
        )

    def __and__(self, other: "PartitionsSubset") -> "PartitionsSubset":
        return other

    def __sub__(self, other: "PartitionsSubset") -> "PartitionsSubset":
        from dagster._core.definitions.partitions.definition import TimeWindowPartitionsDefinition
        from dagster._core.definitions.partitions.subset import TimeWindowPartitionsSubset

        if self == other:
            return self.partitions_def.empty_subset()
        elif isinstance(other, TimeWindowPartitionsSubset) and isinstance(
            self.partitions_def, TimeWindowPartitionsDefinition
        ):
            return TimeWindowPartitionsSubset.from_all_partitions_subset(self) - other
        return self.partitions_def.empty_subset().with_partition_keys(
            set(self.get_partition_keys()).difference(set(other.get_partition_keys()))
        )

    def __or__(self, other: "PartitionsSubset") -> "PartitionsSubset":
        return self

    def __len__(self) -> int:
        return len(self.get_partition_keys())

    def __contains__(self, value) -> bool:
        return self.partitions_def.has_partition_key(
            partition_key=value,
            current_time=self.current_time,
            dynamic_partitions_store=self.dynamic_partitions_store,
        )

    def __repr__(self) -> str:
        return f"AllPartitionsSubset(partitions_def={self.partitions_def})"

    @classmethod
    def can_deserialize(
        cls,
        partitions_def: PartitionsDefinition,
        serialized: str,
        serialized_partitions_def_unique_id: Optional[str],
        serialized_partitions_def_class_name: Optional[str],
    ) -> bool:
        return False

    def serialize(self) -> str:
        raise NotImplementedError()

    @classmethod
    def from_serialized(
        cls, partitions_def: PartitionsDefinition, serialized: str
    ) -> "PartitionsSubset":
        raise NotImplementedError()

    def empty_subset(self) -> PartitionsSubset:
        return self.partitions_def.empty_subset()

    @classmethod
    def create_empty_subset(
        cls, partitions_def: Optional[PartitionsDefinition] = None
    ) -> PartitionsSubset:
        return check.not_none(partitions_def).empty_subset()

    def to_serializable_subset(self) -> PartitionsSubset:
        return self.partitions_def.subset_with_all_partitions(
            current_time=self.current_time, dynamic_partitions_store=self.dynamic_partitions_store
        ).to_serializable_subset()
