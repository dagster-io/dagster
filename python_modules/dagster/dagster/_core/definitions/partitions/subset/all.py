from collections.abc import Iterable, Sequence
from datetime import datetime
from typing import Optional

import dagster._check as check
from dagster._core.definitions.partitions.context import (
    PartitionLoadingContext,
    use_partition_loading_context,
)
from dagster._core.definitions.partitions.definition.partitions_definition import (
    PartitionsDefinition,
)
from dagster._core.definitions.partitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.partitions.subset.partitions_subset import PartitionsSubset


class AllPartitionsSubset(PartitionsSubset):
    """This is an in-memory (i.e. not serializable) convenience class that represents all partitions
    of a given PartitionsDefinition, allowing set operations to be taken without having to load
    all partition keys immediately.
    """

    def __init__(self, partitions_def: PartitionsDefinition, context: PartitionLoadingContext):
        self.partitions_def = partitions_def
        check.invariant(
            context.dynamic_partitions_store is not None,
            "Cannot create an AllPartitionsSubset if a dynamic_partitions_store is "
            "not available in the current PartitionLoadingContext.",
        )
        self._partition_loading_context = context

    @property
    def is_empty(self) -> bool:
        return False

    @use_partition_loading_context
    def get_partition_keys(self, current_time: Optional[datetime] = None) -> Sequence[str]:
        check.param_invariant(current_time is None, "current_time")
        return self.partitions_def.get_partition_keys()

    def get_partition_keys_not_in_subset(
        self, partitions_def: PartitionsDefinition
    ) -> Iterable[str]:
        return []

    @use_partition_loading_context
    def get_partition_key_ranges(
        self, partitions_def: PartitionsDefinition
    ) -> Sequence[PartitionKeyRange]:
        first_key = partitions_def.get_first_partition_key()
        last_key = partitions_def.get_last_partition_key()
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

    @use_partition_loading_context
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

    @use_partition_loading_context
    def __len__(self) -> int:
        return len(self.get_partition_keys())

    @use_partition_loading_context
    def __contains__(self, value) -> bool:
        return self.partitions_def.has_partition_key(partition_key=value)

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

    @use_partition_loading_context
    def to_serializable_subset(self) -> PartitionsSubset:
        return self.partitions_def.subset_with_all_partitions().to_serializable_subset()
