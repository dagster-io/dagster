from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence
from typing import Generic, Optional

from typing_extensions import TypeVar

from dagster._annotations import public
from dagster._core.definitions.partitions.definition.partitions_definition import (
    PartitionsDefinition,
)
from dagster._core.definitions.partitions.partition_key_range import PartitionKeyRange

T_str = TypeVar("T_str", bound=str, default=str, covariant=True)


class PartitionsSubset(ABC, Generic[T_str]):
    """Represents a subset of the partitions within a PartitionsDefinition."""

    @property
    def is_empty(self) -> bool:
        return len(list(self.get_partition_keys())) == 0

    @abstractmethod
    def get_partition_keys_not_in_subset(
        self, partitions_def: PartitionsDefinition[T_str]
    ) -> Iterable[T_str]: ...

    @abstractmethod
    @public
    def get_partition_keys(self) -> Iterable[T_str]: ...

    @abstractmethod
    def get_partition_key_ranges(
        self, partitions_def: PartitionsDefinition
    ) -> Sequence[PartitionKeyRange]: ...

    @abstractmethod
    def with_partition_keys(self, partition_keys: Iterable[str]) -> "PartitionsSubset[T_str]": ...

    def with_partition_key_range(
        self, partitions_def: PartitionsDefinition[T_str], partition_key_range: PartitionKeyRange
    ) -> "PartitionsSubset[T_str]":
        return self.with_partition_keys(
            partitions_def.get_partition_keys_in_range(partition_key_range)
        )

    def __or__(self, other: "PartitionsSubset") -> "PartitionsSubset":
        from dagster._core.definitions.partitions.subset.all import AllPartitionsSubset

        if self is other or other.is_empty:
            return self
        # Anything | AllPartitionsSubset = AllPartitionsSubset
        # (this assumes the two subsets are using the same partitions definition)
        if isinstance(other, AllPartitionsSubset):
            return other
        return self.with_partition_keys(other.get_partition_keys())

    def __sub__(self, other: "PartitionsSubset") -> "PartitionsSubset":
        from dagster._core.definitions.partitions.subset.all import AllPartitionsSubset

        if self is other:
            return self.empty_subset()
        if other.is_empty:
            return self
        # Anything - AllPartitionsSubset = Empty
        # (this assumes the two subsets are using the same partitions definition)
        if isinstance(other, AllPartitionsSubset):
            return self.empty_subset()
        return self.empty_subset().with_partition_keys(
            set(self.get_partition_keys()).difference(set(other.get_partition_keys()))
        )

    def __and__(self, other: "PartitionsSubset") -> "PartitionsSubset":
        from dagster._core.definitions.partitions.subset.all import AllPartitionsSubset

        if self is other:
            return self
        if other.is_empty:
            return other
        # Anything & AllPartitionsSubset = Anything
        # (this assumes the two subsets are using the same partitions definition)
        if isinstance(other, AllPartitionsSubset):
            return self
        return self.empty_subset().with_partition_keys(
            set(self.get_partition_keys()) & set(other.get_partition_keys())
        )

    @abstractmethod
    def serialize(self) -> str: ...

    @classmethod
    @abstractmethod
    def from_serialized(
        cls, partitions_def: PartitionsDefinition[T_str], serialized: str
    ) -> "PartitionsSubset[T_str]": ...

    @classmethod
    @abstractmethod
    def can_deserialize(
        cls,
        partitions_def: PartitionsDefinition,
        serialized: str,
        serialized_partitions_def_unique_id: Optional[str],
        serialized_partitions_def_class_name: Optional[str],
    ) -> bool: ...

    @abstractmethod
    def __len__(self) -> int: ...

    @abstractmethod
    def __contains__(self, value) -> bool: ...

    def empty_subset(self) -> "PartitionsSubset[T_str]": ...

    @classmethod
    @abstractmethod
    def create_empty_subset(
        cls, partitions_def: Optional[PartitionsDefinition] = None
    ) -> "PartitionsSubset[T_str]": ...

    def to_serializable_subset(self) -> "PartitionsSubset":
        return self
