import itertools
import json
from datetime import datetime
from typing import Dict, Iterable, List, Mapping, NamedTuple, Optional, Sequence, Set, Tuple, cast

from collections import defaultdict
import dagster._check as check
from dagster._annotations import experimental
from dagster._core.errors import (
    DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError,
    DagsterInvalidDeserializationVersionError,
)
from dagster._core.storage.tags import (
    MULTIDIMENSIONAL_PARTITION_PREFIX,
    get_multidimensional_partition_tag,
)

from .partition import (
    PartitionsSubset,
    DefaultPartitionsSubset,
    Partition,
    PartitionsDefinition,
    StaticPartitionsDefinition,
    PartitionKeyRange,
)
from .time_window_partitions import TimeWindowPartitionsDefinition, TimeWindowPartitionsSubset

INVALID_STATIC_PARTITIONS_KEY_CHARACTERS = set(["|", ",", "[", "]"])


class PartitionDimensionKey(
    NamedTuple("_PartitionDimensionKey", [("dimension_name", str), ("partition_key", str)])
):
    """
    Representation of a single dimension of a multi-dimensional partition key.
    """

    def __new__(cls, dimension_name: str, partition_key: str):
        return super(PartitionDimensionKey, cls).__new__(
            cls,
            dimension_name=check.str_param(dimension_name, "dimension_name"),
            partition_key=check.str_param(partition_key, "partition_key"),
        )


class MultiPartitionKey(str):
    """
    A multi-dimensional partition key stores the partition key for each dimension.
    Subclasses the string class to keep partition key type as a string.

    Contains additional methods to access the partition key for each dimension.
    Creates a string representation of the partition key for each dimension, separated by a pipe (|).
    Orders the dimensions by name, to ensure consistent string representation.
    """

    dimension_keys: List[PartitionDimensionKey] = []

    def __new__(cls, keys_by_dimension: Mapping[str, str]):
        check.mapping_param(
            keys_by_dimension, "partitions_by_dimension", key_type=str, value_type=str
        )

        dimension_keys: List[PartitionDimensionKey] = [
            PartitionDimensionKey(dimension, keys_by_dimension[dimension])
            for dimension in sorted(list(keys_by_dimension.keys()))
        ]

        str_key = super(MultiPartitionKey, cls).__new__(
            cls, "|".join([dim_key.partition_key for dim_key in dimension_keys])
        )

        str_key.dimension_keys = dimension_keys

        return str_key

    def __getnewargs__(self):
        # When this instance is pickled, replace the argument to __new__ with the
        # dimension key mapping instead of the string representation.
        return ({dim_key.dimension_name: dim_key.partition_key for dim_key in self.dimension_keys},)

    @property
    def keys_by_dimension(self) -> Mapping[str, str]:
        return {dim_key.dimension_name: dim_key.partition_key for dim_key in self.dimension_keys}


class PartitionDimensionDefinition(
    NamedTuple(
        "_PartitionDimensionDefinition",
        [
            ("name", str),
            ("partitions_def", PartitionsDefinition),
        ],
    )
):
    def __new__(
        cls,
        name: str,
        partitions_def: PartitionsDefinition,
    ):
        return super().__new__(
            cls,
            name=check.str_param(name, "name"),
            partitions_def=check.inst_param(partitions_def, "partitions_def", PartitionsDefinition),
        )

    def __eq__(self, other):
        return (
            isinstance(other, PartitionDimensionDefinition)
            and self.name == other.name
            and self.partitions_def == other.partitions_def
        )


@experimental
class MultiPartitionsDefinition(PartitionsDefinition):
    """
    Takes the cross-product of partitions from two partitions definitions.

    For example, with a static partitions definition where the partitions are ["a", "b", "c"]
    and a daily partitions definition, this partitions definition will have the following
    partitions:

    2020-01-01|a
    2020-01-01|b
    2020-01-01|c
    2020-01-02|a
    2020-01-02|b
    ...

    Args:
        partitions_defs (Mapping[str, PartitionsDefinition]):
            A mapping of dimension name to partitions definition. The total set of partitions will
            be the cross-product of the partitions from each PartitionsDefinition.

    Attributes:
        partitions_defs (Sequence[PartitionDimensionDefinition]):
            A sequence of PartitionDimensionDefinition objects, each of which contains a dimension
            name and a PartitionsDefinition. The total set of partitions will be the cross-product
            of the partitions from each PartitionsDefinition. This sequence is ordered by
            dimension name, to ensure consistent ordering of the partitions.
    """

    def __init__(self, partitions_defs: Mapping[str, PartitionsDefinition]):
        if not len(partitions_defs.keys()) == 2:
            raise DagsterInvalidInvocationError(
                "Dagster currently only supports multi-partitions definitions with 2 partitions"
                " definitions. Your multi-partitions definition has"
                f" {len(partitions_defs.keys())} partitions definitions."
            )
        check.mapping_param(
            partitions_defs, "partitions_defs", key_type=str, value_type=PartitionsDefinition
        )

        for dim_name, partitions_def in partitions_defs.items():
            if isinstance(partitions_def, StaticPartitionsDefinition):
                if any(
                    [
                        INVALID_STATIC_PARTITIONS_KEY_CHARACTERS & set(key)
                        for key in partitions_def.get_partition_keys()
                    ]
                ):
                    raise DagsterInvalidDefinitionError(
                        f"Invalid character in partition key for dimension {dim_name}. "
                        "A multi-partitions definition cannot contain partition keys with "
                        "the following characters: |, [, ], ,"
                    )

        self._partitions_defs: List[PartitionDimensionDefinition] = sorted(
            [
                PartitionDimensionDefinition(name, partitions_def)
                for name, partitions_def in partitions_defs.items()
            ],
            key=lambda x: x.name,
        )

    @property
    def partition_dimension_names(self) -> List[str]:
        return [dim_def.name for dim_def in self._partitions_defs]

    @property
    def partitions_defs(self) -> Sequence[PartitionDimensionDefinition]:
        return self._partitions_defs

    def get_partitions(self, current_time: Optional[datetime] = None) -> Sequence[Partition]:
        partition_sequences = [
            partition_dim.partitions_def.get_partitions(current_time=current_time)
            for partition_dim in self._partitions_defs
        ]

        def get_multi_dimensional_partition(partitions_tuple: Tuple[Partition]) -> Partition:
            check.invariant(len(partitions_tuple) == len(self._partitions_defs))

            partitions_by_dimension: Dict[str, Partition] = {
                self._partitions_defs[i].name: partitions_tuple[i]
                for i in range(len(partitions_tuple))
            }

            return Partition(
                value=partitions_by_dimension,
                name=MultiPartitionKey(
                    {
                        dimension_key: partition.name
                        for dimension_key, partition in partitions_by_dimension.items()
                    }
                ),
            )

        return [
            get_multi_dimensional_partition(partitions_tuple)
            for partitions_tuple in itertools.product(*partition_sequences)
        ]

    def __eq__(self, other):
        return (
            isinstance(other, MultiPartitionsDefinition)
            and self.partitions_defs == other.partitions_defs
        )

    def __hash__(self):
        return hash(
            tuple(
                [
                    (partitions_def.name, partitions_def.__repr__())
                    for partitions_def in self.partitions_defs
                ]
            )
        )

    def __str__(self) -> str:
        dimension_1 = self._partitions_defs[0]
        dimension_2 = self._partitions_defs[1]
        partition_str = (
            "Multi-partitioned, with dimensions: \n"
            f"{dimension_1.name.capitalize()}: {str(dimension_1.partitions_def)} \n"
            f"{dimension_2.name.capitalize()}: {str(dimension_2.partitions_def)}"
        )
        return partition_str

    def __repr__(self) -> str:
        return f"{type(self).__name__}(dimensions={[str(dim) for dim in self.partitions_defs]}"

    def split_partition_key_str(self, partition_key_str: str) -> Mapping[str, str]:
        """
        Given a string representation of a partition key, returns a list of per-dimension
        partition keys in the supplied order.

        Does not validate, relying on downstream checks to ensure that the partition key is valid
        for performance reasons.
        """
        check.str_param(partition_key_str, "partition_key_str")

        partition_key_strs = partition_key_str.split("|")
        check.invariant(
            len(partition_key_strs) == len(self.partitions_defs),
            f"Expected {len(self.partitions_defs)} partition keys in partition key string {partition_key_str}, "
            f"but got {len(partition_key_strs)}",
        )

        return {dim.name: partition_key_strs[i] for i, dim in enumerate(self._partitions_defs)}

    def get_multi_partition_key_from_str(self, partition_key_str: str) -> MultiPartitionKey:
        """
        Given a string representation of a partition key, returns a MultiPartitionKey object.
        """
        check.str_param(partition_key_str, "partition_key_str")

        partition_key_strs = partition_key_str.split("|")
        check.invariant(
            len(partition_key_strs) == len(self.partitions_defs),
            (
                f"Expected {len(self.partitions_defs)} partition keys in partition key string"
                f" {partition_key_str}, but got {len(partition_key_strs)}"
            ),
        )
        keys_per_dimension = [
            (dim.name, dim.partitions_def.get_partition_keys()) for dim in self._partitions_defs
        ]

        partition_key_dims_by_idx = dict(enumerate([dim.name for dim in self._partitions_defs]))
        for idx, key in enumerate(partition_key_strs):
            check.invariant(
                key in keys_per_dimension[idx][1],
                f"Partition key {key} not found in dimension {partition_key_dims_by_idx[idx][0]}",
            )

        multi_partition_key = MultiPartitionKey(
            {partition_key_dims_by_idx[idx]: key for idx, key in enumerate(partition_key_strs)}
        )
        return multi_partition_key

    def empty_subset(self) -> "MultiPartitionsSubset":
        return MultiPartitionsSubset(self)

    def deserialize_subset(self, serialized: str) -> "MultiPartitionsSubset":
        return MultiPartitionsSubset.from_serialized(self, serialized)

    def _get_primary_and_secondary_dimension(
        self,
    ) -> Tuple[PartitionDimensionDefinition, PartitionDimensionDefinition]:
        # Multipartitions subsets are serialized by primary dimension. If changing
        # the selection of primary/secondary dimension, will need to also update the
        # serialization of MultiPartitionsSubsets
        partition_defs = self.partitions_defs
        time_partition_defs = [
            dimension_def
            for dimension_def in partition_defs
            if isinstance(dimension_def.partitions_def, TimeWindowPartitionsDefinition)
        ]
        secondary_serialization_dimension = (
            next(iter(time_partition_defs)) if len(time_partition_defs) == 1 else partition_defs[1]
        )
        primary_serialization_dimension = next(
            iter([dim for dim in partition_defs if dim != secondary_serialization_dimension])
        )
        return primary_serialization_dimension, secondary_serialization_dimension

    @property
    def primary_dimension(self) -> PartitionDimensionDefinition:
        return self._get_primary_and_secondary_dimension()[0]

    @property
    def secondary_dimension(self) -> PartitionDimensionDefinition:
        return self._get_primary_and_secondary_dimension()[1]


class MultiPartitionsSubset(PartitionsSubset):
    # Every time we change the serialization format, we should increment the version number.
    # This will ensure that we can deserialize old data.
    SERIALIZATION_VERSION = 1

    def __init__(
        self,
        partitions_def: MultiPartitionsDefinition,
        subsets_by_primary_dimension_partition_key: Optional[Mapping[str, PartitionsSubset]] = None,
    ):
        self._partitions_def = check.inst_param(
            partitions_def, "partitions_def", MultiPartitionsDefinition
        )

        check.opt_mapping_param(
            subsets_by_primary_dimension_partition_key,
            "subsets_by_primary_dimension_partition_key",
            key_type=str,
            value_type=PartitionsSubset,
        )
        if not subsets_by_primary_dimension_partition_key:
            self._subsets_by_primary_dimension_partition_key = {
                primary_key: partitions_def.secondary_dimension.partitions_def.empty_subset()
                for primary_key in partitions_def.primary_dimension.partitions_def.get_partition_keys()
            }
        else:
            check.invariant(
                set(partitions_def.primary_dimension.partitions_def.get_partition_keys())
                == set(subsets_by_primary_dimension_partition_key.keys()),
                f"The provided primary dimension partition keys must equal the set of partition keys of dimension {partitions_def.primary_dimension.name}",
            )
            for secondary_dim_subset in subsets_by_primary_dimension_partition_key.values():
                check.invariant(
                    secondary_dim_subset.partitions_def
                    == partitions_def.secondary_dimension.partitions_def,
                    f"Secondary dimension subset partitions definition {secondary_dim_subset.partitions_def} does not match partitions definition for dimension {partitions_def.secondary_dimension.name}",
                )
            self._subsets_by_primary_dimension_partition_key = (
                subsets_by_primary_dimension_partition_key
            )

    @property
    def partitions_def(self) -> MultiPartitionsDefinition:
        return self._partitions_def

    def get_partition_keys_not_in_subset(
        self, current_time: Optional[datetime] = None
    ) -> Iterable[str]:
        keys_not_in_subset = set()
        for (
            primary_key,
            secondary_subset,
        ) in self._subsets_by_primary_dimension_partition_key.items():
            for secondary_key in secondary_subset.get_partition_keys_not_in_subset(current_time):
                keys_not_in_subset.add(
                    MultiPartitionKey(
                        {
                            self.partitions_def.primary_dimension.name: primary_key,
                            self.partitions_def.secondary_dimension.name: secondary_key,
                        }
                    )
                )
        return keys_not_in_subset

    def get_partition_keys(self, current_time: Optional[datetime] = None) -> Iterable[str]:
        keys_in_subset = set()
        for (
            primary_key,
            secondary_subset,
        ) in self._subsets_by_primary_dimension_partition_key.items():
            for secondary_key in secondary_subset.get_partition_keys(current_time):
                keys_in_subset.add(
                    MultiPartitionKey(
                        {
                            self.partitions_def.primary_dimension.name: primary_key,
                            self.partitions_def.secondary_dimension.name: secondary_key,
                        }
                    )
                )
        return keys_in_subset

    def get_partition_key_ranges(
        self, current_time: Optional[datetime] = None
    ) -> Sequence[PartitionKeyRange]:
        partition_keys = self._partitions_def.get_partition_keys(current_time)
        cur_range_start = None
        cur_range_end = None
        result = []
        for partition_key in partition_keys:
            if partition_key in self:
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

    def __eq__(self, other):
        return (
            isinstance(other, MultiPartitionsSubset)
            and self.partitions_def == other.partitions_def
            and self._subsets_by_primary_dimension_partition_key
            == other._subsets_by_primary_dimension_partition_key
        )

    def __len__(self) -> int:
        return sum(
            len(subset) for subset in self._subsets_by_primary_dimension_partition_key.values()
        )

    def __contains__(self, partition_key: str) -> bool:
        if not isinstance(partition_key, MultiPartitionKey):
            check.failed("partition_key must be a MultiPartitionKey")

        primary_key = partition_key.keys_by_dimension.get(
            self.partitions_def.primary_dimension.name
        )
        secondary_key = partition_key.keys_by_dimension.get(
            self.partitions_def.secondary_dimension.name
        )
        return (
            primary_key is not None
            and primary_key in self._subsets_by_primary_dimension_partition_key
            and secondary_key is not None
            and secondary_key in self._subsets_by_primary_dimension_partition_key[primary_key]
        )

    def with_partition_keys(self, partition_keys: Iterable[str]) -> "MultiPartitionsSubset":
        new_keys_by_primary_dim_key = defaultdict(set)
        keys_split_into_dimensions = [
            self._partitions_def.split_partition_key_str(key) for key in partition_keys
        ]

        for dim_key_mapping in keys_split_into_dimensions:
            new_keys_by_primary_dim_key[
                dim_key_mapping[self.partitions_def.primary_dimension.name]
            ].add(dim_key_mapping[self.partitions_def.secondary_dimension.name])

        if isinstance(
            self.partitions_def.secondary_dimension.partitions_def, TimeWindowPartitionsDefinition
        ):
            secondary_dim_def = self.partitions_def.secondary_dimension.partitions_def
            # Cache the valid time windows to avoid refetching them for creating each time window subset.
            # Fetching the valid time windows is expensive.
            _valid_time_windows = list(
                secondary_dim_def.iterate_valid_time_windows(start=secondary_dim_def.start)
            )

            return MultiPartitionsSubset(
                self._partitions_def,
                {
                    primary_key: cast(
                        TimeWindowPartitionsSubset, secondary_dim_subset
                    ).with_partition_keys(
                        new_keys_by_primary_dim_key[primary_key],
                        _valid_time_windows=_valid_time_windows,
                    )
                    for primary_key, secondary_dim_subset in self._subsets_by_primary_dimension_partition_key.items()
                },
            )
        else:
            return MultiPartitionsSubset(
                self._partitions_def,
                {
                    primary_key: secondary_dim_subset.with_partition_keys(
                        new_keys_by_primary_dim_key[primary_key],
                    )
                    for primary_key, secondary_dim_subset in self._subsets_by_primary_dimension_partition_key.items()
                },
            )

    def serialize(self) -> str:
        # Serialize version number, so attempting to deserialize old versions can be handled gracefully.
        # Any time the serialization format changes, we should increment the version number.
        return json.dumps(
            {
                "version": self.SERIALIZATION_VERSION,
                "serialized_subsets_by_primary_key": {
                    primary_key: secondary_dim_subset.serialize()
                    for primary_key, secondary_dim_subset in self._subsets_by_primary_dimension_partition_key.items()
                },
            }
        )

    @classmethod
    def can_deserialize(cls, serialized: str) -> bool:
        # Check the version number to determine if the serialization format is supported
        data = json.loads(serialized)
        return data.get("version") == cls.SERIALIZATION_VERSION

    @classmethod
    def from_serialized(
        cls, partitions_def: PartitionsDefinition, serialized: str
    ) -> "MultiPartitionsSubset":
        if not isinstance(partitions_def, MultiPartitionsDefinition):
            check.failed(
                "Must pass a MultiPartitionsDefinition object to deserialize MultiPartitionsSubset."
            )

        data = json.loads(serialized)
        if data.get("version") != cls.SERIALIZATION_VERSION:
            raise DagsterInvalidDeserializationVersionError(
                f"Attempted to deserialize partition subset with version {data.get('version')}, but only version {cls.SERIALIZATION_VERSION} is supported."
            )

        return MultiPartitionsSubset(
            partitions_def=partitions_def,
            subsets_by_primary_dimension_partition_key={
                primary_key: partitions_def.secondary_dimension.partitions_def.deserialize_subset(
                    subset
                )
                for primary_key, subset in data["serialized_subsets_by_primary_key"].items()
            },
        )

    def get_inverse_subset(self) -> "MultiPartitionsSubset":
        if isinstance(
            self.partitions_def.secondary_dimension.partitions_def, TimeWindowPartitionsDefinition
        ):
            secondary_dim_def = self.partitions_def.secondary_dimension.partitions_def
            # Cache the valid time windows to avoid refetching them for creating each time window subset.
            # Fetching the valid time windows is expensive.
            _valid_time_windows = list(
                secondary_dim_def.iterate_valid_time_windows(start=secondary_dim_def.start)
            )

            return MultiPartitionsSubset(
                partitions_def=self._partitions_def,
                subsets_by_primary_dimension_partition_key={
                    primary_key: cast(
                        TimeWindowPartitionsSubset, secondary_dim_subset
                    ).get_inverse_subset(_valid_time_windows)
                    for primary_key, secondary_dim_subset in self._subsets_by_primary_dimension_partition_key.items()
                },
            )
        else:
            return MultiPartitionsSubset(
                partitions_def=self._partitions_def,
                subsets_by_primary_dimension_partition_key={
                    primary_key: secondary_dim_subset.get_inverse_subset()
                    for primary_key, secondary_dim_subset in self._subsets_by_primary_dimension_partition_key.items()
                },
            )

    @property
    def subsets_by_primary_dimension_partition_key(self) -> Mapping[str, PartitionsSubset]:
        return self._subsets_by_primary_dimension_partition_key


def get_tags_from_multi_partition_key(multi_partition_key: MultiPartitionKey) -> Mapping[str, str]:
    check.inst_param(multi_partition_key, "multi_partition_key", MultiPartitionKey)

    return {
        get_multidimensional_partition_tag(dimension.dimension_name): dimension.partition_key
        for dimension in multi_partition_key.dimension_keys
    }


def get_multipartition_key_from_tags(tags: Mapping[str, str]) -> str:
    partitions_by_dimension: Dict[str, str] = {}
    for tag in tags:
        if tag.startswith(MULTIDIMENSIONAL_PARTITION_PREFIX):
            dimension = tag[len(MULTIDIMENSIONAL_PARTITION_PREFIX) :]
            partitions_by_dimension[dimension] = tags[tag]

    return MultiPartitionKey(partitions_by_dimension)
