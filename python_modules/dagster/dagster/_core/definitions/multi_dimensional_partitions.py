import hashlib
import itertools
from datetime import datetime
from functools import lru_cache, reduce
from typing import (
    Dict,
    Iterable,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    Union,
    cast,
)

import pendulum

import dagster._check as check
from dagster._annotations import public
from dagster._core.errors import (
    DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError,
    DagsterUnknownPartitionError,
)
from dagster._core.instance import DynamicPartitionsStore
from dagster._core.storage.tags import (
    MULTIDIMENSIONAL_PARTITION_PREFIX,
    get_multidimensional_partition_tag,
)

from .partition import (
    DefaultPartitionsSubset,
    DynamicPartitionsDefinition,
    PartitionsDefinition,
    PartitionsSubset,
    StaticPartitionsDefinition,
)
from .time_window_partitions import TimeWindow, TimeWindowPartitionsDefinition

INVALID_STATIC_PARTITIONS_KEY_CHARACTERS = set(["|", ",", "[", "]"])

MULTIPARTITION_KEY_DELIMITER = "|"


class PartitionDimensionKey(
    NamedTuple("_PartitionDimensionKey", [("dimension_name", str), ("partition_key", str)])
):
    """Representation of a single dimension of a multi-dimensional partition key."""

    def __new__(cls, dimension_name: str, partition_key: str):
        return super(PartitionDimensionKey, cls).__new__(
            cls,
            dimension_name=check.str_param(dimension_name, "dimension_name"),
            partition_key=check.str_param(partition_key, "partition_key"),
        )


class MultiPartitionKey(str):
    """A multi-dimensional partition key stores the partition key for each dimension.
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
            cls,
            MULTIPARTITION_KEY_DELIMITER.join(
                [dim_key.partition_key for dim_key in dimension_keys]
            ),
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

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, PartitionDimensionDefinition)
            and self.name == other.name
            and self.partitions_def == other.partitions_def
        )


ALLOWED_PARTITION_DIMENSION_TYPES = (
    StaticPartitionsDefinition,
    TimeWindowPartitionsDefinition,
    DynamicPartitionsDefinition,
)


def _check_valid_partitions_dimensions(
    partitions_dimensions: Mapping[str, PartitionsDefinition]
) -> None:
    for dim_name, partitions_def in partitions_dimensions.items():
        if not any(isinstance(partitions_def, t) for t in ALLOWED_PARTITION_DIMENSION_TYPES):
            raise DagsterInvalidDefinitionError(
                f"Invalid partitions definition type {type(partitions_def)}. "
                "Only the following partitions definition types are supported: "
                f"{ALLOWED_PARTITION_DIMENSION_TYPES}."
            )
        if isinstance(partitions_def, DynamicPartitionsDefinition) and partitions_def.name is None:
            raise DagsterInvalidDefinitionError(
                "DynamicPartitionsDefinition must have a name to be used in a"
                " MultiPartitionsDefinition."
            )

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


class MultiPartitionsDefinition(PartitionsDefinition[MultiPartitionKey]):
    """Takes the cross-product of partitions from two partitions definitions.

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

        _check_valid_partitions_dimensions(partitions_defs)

        self._partitions_defs: List[PartitionDimensionDefinition] = sorted(
            [
                PartitionDimensionDefinition(name, partitions_def)
                for name, partitions_def in partitions_defs.items()
            ],
            key=lambda x: x.name,
        )

    @property
    def partitions_subset_class(self) -> Type["PartitionsSubset"]:
        return MultiPartitionsSubset

    def get_serializable_unique_identifier(
        self, dynamic_partitions_store: Optional[DynamicPartitionsStore] = None
    ) -> str:
        return hashlib.sha1(
            str(
                {
                    dim_def.name: dim_def.partitions_def.get_serializable_unique_identifier(
                        dynamic_partitions_store
                    )
                    for dim_def in self.partitions_defs
                }
            ).encode("utf-8")
        ).hexdigest()

    @property
    def partition_dimension_names(self) -> List[str]:
        return [dim_def.name for dim_def in self._partitions_defs]

    @property
    def partitions_defs(self) -> Sequence[PartitionDimensionDefinition]:
        return self._partitions_defs

    def get_partitions_def_for_dimension(self, dimension_name: str) -> PartitionsDefinition:
        for dim_def in self._partitions_defs:
            if dim_def.name == dimension_name:
                return dim_def.partitions_def
        check.failed(f"Invalid dimension name {dimension_name}")

    # We override the default implementation of `has_partition_key` for performance.
    def has_partition_key(
        self,
        partition_key: Union[MultiPartitionKey, str],
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> bool:
        partition_key = (
            partition_key
            if isinstance(partition_key, MultiPartitionKey)
            else self.get_partition_key_from_str(partition_key)
        )
        if partition_key.keys_by_dimension.keys() != set(self.partition_dimension_names):
            raise DagsterUnknownPartitionError(
                f"Invalid partition key {partition_key}. The dimensions of the partition key are"
                " not the dimensions of the partitions definition."
            )

        for dimension in self.partitions_defs:
            if not dimension.partitions_def.has_partition_key(
                partition_key.keys_by_dimension[dimension.name],
                current_time=current_time,
                dynamic_partitions_store=dynamic_partitions_store,
            ):
                return False
        return True

    @lru_cache(maxsize=5)
    def _get_partition_keys(
        self, current_time: datetime, dynamic_partitions_store: Optional[DynamicPartitionsStore]
    ) -> Sequence[MultiPartitionKey]:
        partition_key_sequences = [
            partition_dim.partitions_def.get_partition_keys(
                current_time=current_time, dynamic_partitions_store=dynamic_partitions_store
            )
            for partition_dim in self._partitions_defs
        ]

        return [
            MultiPartitionKey(
                {self._partitions_defs[i].name: key for i, key in enumerate(partition_key_tuple)}
            )
            for partition_key_tuple in itertools.product(*partition_key_sequences)
        ]

    @public
    def get_partition_keys(
        self,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> Sequence[MultiPartitionKey]:
        """Returns a list of MultiPartitionKeys representing the partition keys of the
        PartitionsDefinition.

        Args:
            current_time (Optional[datetime]): A datetime object representing the current time, only
                applicable to time-based partition dimensions.
            dynamic_partitions_store (Optional[DynamicPartitionsStore]): The DynamicPartitionsStore
                object that is responsible for fetching dynamic partitions. Required when a
                dimension is a DynamicPartitionsDefinition with a name defined. Users can pass the
                DagsterInstance fetched via `context.instance` to this argument.

        Returns:
            Sequence[MultiPartitionKey]
        """
        return self._get_partition_keys(
            current_time or pendulum.now("UTC"), dynamic_partitions_store
        )

    def filter_valid_partition_keys(
        self, partition_keys: Set[str], dynamic_partitions_store: DynamicPartitionsStore
    ) -> Set[MultiPartitionKey]:
        partition_keys_by_dimension = {
            dim.name: dim.partitions_def.get_partition_keys(
                dynamic_partitions_store=dynamic_partitions_store
            )
            for dim in self.partitions_defs
        }
        validated_partitions = set()
        for partition_key in partition_keys:
            partition_key_strs = partition_key.split(MULTIPARTITION_KEY_DELIMITER)
            if len(partition_key_strs) != len(self.partitions_defs):
                continue

            multipartition_key = MultiPartitionKey(
                {dim.name: partition_key_strs[i] for i, dim in enumerate(self._partitions_defs)}
            )

            if all(
                key in partition_keys_by_dimension.get(dim, [])
                for dim, key in multipartition_key.keys_by_dimension.items()
            ):
                validated_partitions.add(partition_key)

        return validated_partitions

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
            f"{dimension_1.name.capitalize()}: {dimension_1.partitions_def} \n"
            f"{dimension_2.name.capitalize()}: {dimension_2.partitions_def}"
        )
        return partition_str

    def __repr__(self) -> str:
        return f"{type(self).__name__}(dimensions={[str(dim) for dim in self.partitions_defs]}"

    def get_partition_key_from_str(self, partition_key_str: str) -> MultiPartitionKey:
        """Given a string representation of a partition key, returns a MultiPartitionKey object."""
        check.str_param(partition_key_str, "partition_key_str")

        partition_key_strs = partition_key_str.split(MULTIPARTITION_KEY_DELIMITER)
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

    def get_tags_for_partition_key(self, partition_key: str) -> Mapping[str, str]:
        partition_key = cast(MultiPartitionKey, self.get_partition_key_from_str(partition_key))
        tags = {**super().get_tags_for_partition_key(partition_key)}
        tags.update(get_tags_from_multi_partition_key(partition_key))
        return tags

    @property
    def time_window_dimension(self) -> PartitionDimensionDefinition:
        time_window_dims = [
            dim
            for dim in self.partitions_defs
            if isinstance(dim.partitions_def, TimeWindowPartitionsDefinition)
        ]
        check.invariant(
            len(time_window_dims) == 1, "Expected exactly one time window partitioned dimension"
        )
        return next(iter(time_window_dims))

    def time_window_for_partition_key(self, partition_key: str) -> TimeWindow:
        if not isinstance(partition_key, MultiPartitionKey):
            partition_key = self.get_partition_key_from_str(partition_key)

        time_window_dimension = self.time_window_dimension
        return cast(
            TimeWindowPartitionsDefinition, time_window_dimension.partitions_def
        ).time_window_for_partition_key(
            cast(MultiPartitionKey, partition_key).keys_by_dimension[time_window_dimension.name]
        )

    def get_multipartition_keys_with_dimension_value(
        self,
        dimension_name: str,
        dimension_partition_key: str,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
        current_time: Optional[datetime] = None,
    ) -> Sequence[MultiPartitionKey]:
        check.str_param(dimension_name, "dimension_name")
        check.str_param(dimension_partition_key, "dimension_partition_key")

        matching_dimensions = [
            dimension for dimension in self.partitions_defs if dimension.name == dimension_name
        ]
        other_dimensions = [
            dimension for dimension in self.partitions_defs if dimension.name != dimension_name
        ]

        check.invariant(
            len(matching_dimensions) == 1,
            (
                f"Dimension {dimension_name} not found in MultiPartitionsDefinition with dimensions"
                f" {[dim.name for dim in self.partitions_defs]}"
            ),
        )

        partition_sequences = [
            partition_dim.partitions_def.get_partition_keys(
                current_time=current_time, dynamic_partitions_store=dynamic_partitions_store
            )
            for partition_dim in other_dimensions
        ] + [[dimension_partition_key]]

        # Names of partitions dimensions in the same order as partition_sequences
        partition_dim_names = [dim.name for dim in other_dimensions] + [dimension_name]

        return [
            MultiPartitionKey(
                {
                    partition_dim_names[i]: partition_key
                    for i, partition_key in enumerate(partitions_tuple)
                }
            )
            for partitions_tuple in itertools.product(*partition_sequences)
        ]

    def get_num_partitions(
        self,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> int:
        # Static partitions definitions can contain duplicate keys (will throw error in 1.3.0)
        # In the meantime, relying on get_num_partitions to handle duplicates to display
        # correct counts in the Dagster UI.
        dimension_counts = [
            dim.partitions_def.get_num_partitions(
                current_time=current_time, dynamic_partitions_store=dynamic_partitions_store
            )
            for dim in self.partitions_defs
        ]
        return reduce(lambda x, y: x * y, dimension_counts, 1)


class MultiPartitionsSubset(DefaultPartitionsSubset):
    def __init__(
        self,
        partitions_def: MultiPartitionsDefinition,
        subset: Optional[Set[str]] = None,
    ):
        check.inst_param(partitions_def, "partitions_def", MultiPartitionsDefinition)
        subset = (
            set(
                [
                    partitions_def.get_partition_key_from_str(key)
                    for key in subset
                    if MULTIPARTITION_KEY_DELIMITER in key
                ]
            )
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
