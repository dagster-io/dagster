import itertools
from datetime import datetime
from typing import Dict, Iterable, List, Mapping, NamedTuple, Optional, Sequence, Set, Tuple, cast

import dagster._check as check
from dagster._annotations import experimental
from dagster._core.errors import (
    DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError,
)
from dagster._core.storage.tags import (
    MULTIDIMENSIONAL_PARTITION_PREFIX,
    get_multidimensional_partition_tag,
)

from .partition import (
    DefaultPartitionsSubset,
    Partition,
    PartitionsDefinition,
    PartitionsSubset,
    StaticPartitionsDefinition,
)
from .time_window_partitions import TimeWindowPartitionsDefinition

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

    def get_partition_key_from_str(self, partition_key_str: str) -> str:
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

        return MultiPartitionKey(
            {dim.name: partition_key_strs[i] for i, dim in enumerate(self._partitions_defs)}
        )

    def empty_subset(self) -> "MultiPartitionsSubset":
        return MultiPartitionsSubset(self, set())

    def deserialize_subset(self, serialized: str) -> "PartitionsSubset":
        return MultiPartitionsSubset.from_serialized(self, serialized)

    def _get_primary_and_secondary_dimension(
        self,
    ) -> Tuple[PartitionDimensionDefinition, PartitionDimensionDefinition]:
        # Multipartitions subsets are serialized by primary dimension. If changing
        # the selection of primary/secondary dimension, will need to also update the
        # serialization of MultiPartitionsSubsets

        time_dimensions = [
            dim
            for dim in self.partitions_defs
            if isinstance(dim.partitions_def, TimeWindowPartitionsDefinition)
        ]
        if len(time_dimensions) == 1:
            primary_dimension, secondary_dimension = time_dimensions[0], next(
                iter([dim for dim in self.partitions_defs if dim != time_dimensions[0]])
            )
        else:
            primary_dimension, secondary_dimension = (
                self.partitions_defs[0],
                self.partitions_defs[1],
            )

        return primary_dimension, secondary_dimension

    @property
    def primary_dimension(self) -> PartitionDimensionDefinition:
        return self._get_primary_and_secondary_dimension()[0]

    @property
    def secondary_dimension(self) -> PartitionDimensionDefinition:
        return self._get_primary_and_secondary_dimension()[1]


class MultiPartitionsSubset(DefaultPartitionsSubset):
    def __init__(
        self,
        partitions_def: MultiPartitionsDefinition,
        subset: Optional[Set[str]] = None,
    ):
        check.inst_param(partitions_def, "partitions_def", MultiPartitionsDefinition)
        subset = (
            set(partitions_def.get_partition_key_from_str(key) for key in subset)
            if subset
            else set()
        )
        super(MultiPartitionsSubset, self).__init__(partitions_def, subset)

    def with_partition_keys(self, partition_keys: Iterable[str]) -> "MultiPartitionsSubset":
        return MultiPartitionsSubset(
            cast(MultiPartitionsDefinition, self._partitions_def),
            self._subset | set(partition_keys),
        )


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
