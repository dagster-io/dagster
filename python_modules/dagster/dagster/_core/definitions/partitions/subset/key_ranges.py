from collections.abc import Iterable, Sequence
from typing import Optional

from dagster_shared.serdes.serdes import deserialize_value

import dagster._check as check
from dagster._core.definitions.partitions.context import require_full_partition_loading_context
from dagster._core.definitions.partitions.definition.partitions_definition import (
    PartitionsDefinition,
)
from dagster._core.definitions.partitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.partitions.snap import PartitionsSnap
from dagster._core.definitions.partitions.subset.default import DefaultPartitionsSubset
from dagster._core.definitions.partitions.subset.partitions_subset import PartitionsSubset
from dagster._record import record
from dagster._serdes import serialize_value, whitelist_for_serdes


@whitelist_for_serdes
@record
class KeyRangesPartitionsSubset(PartitionsSubset):
    key_ranges: Sequence[PartitionKeyRange]
    partitions_snap: PartitionsSnap

    @require_full_partition_loading_context
    def get_partition_keys_not_in_subset(
        self, partitions_def: PartitionsDefinition
    ) -> Iterable[str]:
        partition_key_set = set(self.get_partition_keys())
        return [key for key in partitions_def.get_partition_keys() if key not in partition_key_set]

    @property
    def is_empty(self) -> bool:
        return len(self.key_ranges) == 0

    @property
    def partitions_definition(self) -> PartitionsDefinition:
        return self.partitions_snap.get_partitions_definition()

    @property
    def partition_key_ranges(self) -> Sequence[PartitionKeyRange]:
        return self.key_ranges

    def get_partition_key_ranges(
        self, partitions_def: PartitionsDefinition
    ) -> Sequence[PartitionKeyRange]:
        return self.key_ranges

    @require_full_partition_loading_context
    def get_partition_keys(self) -> Iterable[str]:
        keys = []
        for partition_key_range in self.key_ranges:
            keys.extend(self.partitions_definition.get_partition_keys_in_range(partition_key_range))
        return keys

    @require_full_partition_loading_context
    def with_partition_keys(self, partition_keys: Iterable[str]) -> "PartitionsSubset[str]":
        return DefaultPartitionsSubset({*self.get_partition_keys(), *partition_keys})

    def serialize(self) -> str:
        return serialize_value(self)

    @classmethod
    def from_serialized(
        cls, partitions_def: PartitionsDefinition, serialized: str
    ) -> "PartitionsSubset":
        return deserialize_value(serialized, KeyRangesPartitionsSubset)

    @classmethod
    def can_deserialize(
        cls,
        partitions_def: PartitionsDefinition,
        serialized: str,
        serialized_partitions_def_unique_id: Optional[str],
        serialized_partitions_def_class_name: Optional[str],
    ) -> bool:
        return True

    @require_full_partition_loading_context
    def __len__(self) -> int:
        return sum(
            [
                len(self.partitions_definition.get_partition_keys_in_range(partition_key_range))
                for partition_key_range in self.key_ranges
            ]
        )

    @require_full_partition_loading_context
    def __contains__(self, value) -> bool:
        return value in self.get_partition_keys()

    @classmethod
    def create_empty_subset(
        cls, partitions_def: Optional[PartitionsDefinition] = None
    ) -> "KeyRangesPartitionsSubset":
        return KeyRangesPartitionsSubset(
            key_ranges=[], partitions_snap=PartitionsSnap.from_def(check.not_none(partitions_def))
        )

    def empty_subset(
        self,
    ) -> "KeyRangesPartitionsSubset":
        return KeyRangesPartitionsSubset(key_ranges=[], partitions_snap=self.partitions_snap)
