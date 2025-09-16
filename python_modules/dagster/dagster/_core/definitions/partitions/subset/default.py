import json
from collections.abc import Iterable, Sequence, Set
from typing import NamedTuple, Optional

import dagster._check as check
from dagster._core.definitions.partitions.definition.partitions_definition import (
    PartitionsDefinition,
)
from dagster._core.definitions.partitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.partitions.subset.partitions_subset import PartitionsSubset
from dagster._core.errors import DagsterInvalidDeserializationVersionError
from dagster._serdes import whitelist_for_serdes


@whitelist_for_serdes
class DefaultPartitionsSubset(
    PartitionsSubset,
    NamedTuple("_DefaultPartitionsSubset", [("subset", Set[str])]),
):
    # Every time we change the serialization format, we should increment the version number.
    # This will ensure that we can gracefully degrade when deserializing old data.
    SERIALIZATION_VERSION = 1

    def __new__(
        cls,
        subset: Optional[Set[str]] = None,
    ):
        check.opt_set_param(subset, "subset")
        return super().__new__(cls, subset or set())

    @property
    def is_empty(self) -> bool:
        return len(self.subset) == 0

    def get_partition_keys_not_in_subset(
        self, partitions_def: PartitionsDefinition
    ) -> Iterable[str]:
        return [key for key in partitions_def.get_partition_keys() if key not in self.subset]

    def get_partition_keys(self) -> Iterable[str]:
        return self.subset

    def __sub__(self, other: "PartitionsSubset") -> "PartitionsSubset":
        if not isinstance(other, DefaultPartitionsSubset):
            return super().__sub__(other)

        if self is other:
            return self.empty_subset()
        if other.is_empty:
            return self

        return DefaultPartitionsSubset(self.subset - other.subset)

    def __or__(self, other: "PartitionsSubset") -> "PartitionsSubset":
        if not isinstance(other, DefaultPartitionsSubset):
            return super().__or__(other)

        if self is other or other.is_empty:
            return self

        if self.is_empty:
            return other

        return DefaultPartitionsSubset(self.subset | other.subset)

    def __and__(self, other: "PartitionsSubset") -> "PartitionsSubset":
        if not isinstance(other, DefaultPartitionsSubset):
            return super().__and__(other)

        if self is other:
            return self
        if other.is_empty:
            return other
        if self.is_empty:
            return self

        return DefaultPartitionsSubset(self.subset & other.subset)

    def get_ranges_for_keys(self, partition_keys: Sequence[str]) -> Sequence[PartitionKeyRange]:
        cur_range_start = None
        cur_range_end = None
        result = []
        for partition_key in partition_keys:
            if partition_key in self.subset:
                if cur_range_start is None:
                    cur_range_start = partition_key
                cur_range_end = partition_key
            else:
                if cur_range_start is not None and cur_range_end is not None:
                    result.append(PartitionKeyRange(cur_range_start, cur_range_end))
                cur_range_start = cur_range_end = None

        if cur_range_start is not None and cur_range_end is not None:
            result.append(PartitionKeyRange(cur_range_start, cur_range_end))
        return result

    def get_partition_key_ranges(
        self, partitions_def: PartitionsDefinition
    ) -> Sequence[PartitionKeyRange]:
        from dagster._core.definitions.partitions.definition.multi import MultiPartitionsDefinition

        if isinstance(partitions_def, MultiPartitionsDefinition):
            # For multi-partitions, we construct the ranges by holding one dimension constant
            # and constructing the range for the other dimension
            primary_dimension = partitions_def.primary_dimension
            secondary_dimension = partitions_def.secondary_dimension

            primary_keys_in_subset = set()
            secondary_keys_in_subset = set()
            for partition_key in self.subset:
                primary_keys_in_subset.add(
                    partitions_def.get_partition_key_from_str(partition_key).keys_by_dimension[
                        primary_dimension.name
                    ]
                )
                secondary_keys_in_subset.add(
                    partitions_def.get_partition_key_from_str(partition_key).keys_by_dimension[
                        secondary_dimension.name
                    ]
                )

            # for efficiency, group the keys by whichever dimension has fewer distinct keys
            grouping_dimension = (
                primary_dimension
                if len(primary_keys_in_subset) <= len(secondary_keys_in_subset)
                else secondary_dimension
            )
            grouping_keys = (
                primary_keys_in_subset
                if grouping_dimension == primary_dimension
                else secondary_keys_in_subset
            )

            results = []
            for grouping_key in grouping_keys:
                keys = partitions_def.get_multipartition_keys_with_dimension_value(
                    dimension_name=grouping_dimension.name,
                    dimension_partition_key=grouping_key,
                )
                results.extend(self.get_ranges_for_keys(keys))
            return results

        else:
            partition_keys = partitions_def.get_partition_keys()

            return self.get_ranges_for_keys(partition_keys)

    def with_partition_keys(self, partition_keys: Iterable[str]) -> "DefaultPartitionsSubset":
        return DefaultPartitionsSubset(
            self.subset | set(partition_keys),
        )

    def serialize(self) -> str:
        # Serialize version number, so attempting to deserialize old versions can be handled gracefully.
        # Any time the serialization format changes, we should increment the version number.
        return json.dumps(
            {
                "version": self.SERIALIZATION_VERSION,
                # sort to ensure that equivalent partition subsets have identical serialized forms
                "subset": sorted(list(self.subset)),
            }
        )

    @classmethod
    def from_serialized(
        cls, partitions_def: PartitionsDefinition, serialized: str
    ) -> "PartitionsSubset":
        # Check the version number, so only valid versions can be deserialized.
        data = json.loads(serialized)

        if isinstance(data, list):
            # backwards compatibility
            return cls(subset=set(data))
        else:
            if data.get("version") != cls.SERIALIZATION_VERSION:
                raise DagsterInvalidDeserializationVersionError(
                    f"Attempted to deserialize partition subset with version {data.get('version')},"
                    f" but only version {cls.SERIALIZATION_VERSION} is supported."
                )
            return cls(subset=set(data.get("subset")))

    @classmethod
    def can_deserialize(
        cls,
        partitions_def: PartitionsDefinition,
        serialized: str,
        serialized_partitions_def_unique_id: Optional[str],
        serialized_partitions_def_class_name: Optional[str],
    ) -> bool:
        if serialized_partitions_def_class_name is not None:
            return serialized_partitions_def_class_name == partitions_def.__class__.__name__

        data = json.loads(serialized)
        return isinstance(data, list) or (
            data.get("subset") is not None and data.get("version") == cls.SERIALIZATION_VERSION
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, DefaultPartitionsSubset) and self.subset == other.subset

    def __len__(self) -> int:
        return len(self.subset)

    def __contains__(self, value) -> bool:
        return value in self.subset

    def __repr__(self) -> str:
        return f"DefaultPartitionsSubset(subset={self.subset})"

    @classmethod
    def create_empty_subset(
        cls, partitions_def: Optional[PartitionsDefinition] = None
    ) -> "DefaultPartitionsSubset":
        return cls()

    def empty_subset(
        self,
    ) -> "DefaultPartitionsSubset":
        return DefaultPartitionsSubset()
