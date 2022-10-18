import itertools
from datetime import datetime
from typing import Dict, List, Mapping, NamedTuple, Optional, Sequence, Tuple, TypeVar, Union, cast

import dagster._check as check
from dagster import DagsterInvalidInvocationError
from dagster._serdes import whitelist_for_serdes
from dagster._serdes.serdes import (
    deserialize_json_to_dagster_namedtuple,
    serialize_dagster_namedtuple,
)

from .partition import Partition, PartitionsDefinition


@whitelist_for_serdes
class PartitionDimensionKey(
    NamedTuple(
        "_PartitionDimensionKey",
        [
            ("dimension_name", str),
            ("partition_key", str),
        ],
    )
):
    """
    Serializable representation of a single dimension of a multi-dimensional partition key.
    """

    def __new__(cls, dimension_name: str, partition_key: str):
        return super(PartitionDimensionKey, cls).__new__(
            cls,
            dimension_name=check.str_param(dimension_name, "dimension_name"),
            partition_key=check.str_param(partition_key, "partition_key"),
        )


@whitelist_for_serdes
class MultiDimensionalPartitionKey(
    NamedTuple("_MultiDimensionalPartitionKey", [("dimension_keys", List[PartitionDimensionKey])])
):
    """
    Serializable representation of a multi-dimensional partition key.

    This object is stored as the partition key for asset materialization events.
    Dimension keys are ordered by dimension name, to ensure equivalence regardless
    of user-provided ordering.
    """

    def __new__(cls, dimension_keys: Sequence[PartitionDimensionKey]):
        dimension_keys = check.sequence_param(
            dimension_keys, "dimension_keys", of_type=PartitionDimensionKey
        )
        sorted_keys = list(sorted(dimension_keys, key=lambda key: key.dimension_name))
        return super(MultiDimensionalPartitionKey, cls).__new__(
            cls,
            dimension_keys=sorted_keys,
        )

    def __hash__(self):
        return hash(tuple(self.dimension_keys))

    @staticmethod
    def from_partition_dimension_mapping(
        partition_dimension_mapping: Mapping[str, str],
    ) -> "MultiDimensionalPartitionKey":
        return MultiDimensionalPartitionKey(
            dimension_keys=[
                PartitionDimensionKey(dimension_name, partition_key)
                for dimension_name, partition_key in partition_dimension_mapping.items()
            ]
        )

    def to_db_string(self):
        return serialize_dagster_namedtuple(self)


def deserialize_partition_from_db_string(
    partition: Optional[str],
) -> Optional[Union[str, MultiDimensionalPartitionKey]]:
    if partition is None:
        return None
    if partition.startswith("["):
        return deserialize_json_to_dagster_namedtuple(partition, MultiDimensionalPartitionKey)
    return partition


class MultiDimensionalPartition(Partition):
    def __init__(self, value: Mapping[str, Partition], name: Optional[str] = None):
        self._value = check.mapping_param(value, "value", key_type=str, value_type=Partition)
        self._name = cast(str, check.opt_str_param(name, "name", str(value)))

    @property
    def value(self) -> Mapping[str, Partition]:
        return self._value

    @property
    def name(self) -> str:
        return self._name

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, MultiDimensionalPartition)
            and self.value == other.value
            and self.name == other.name
        )

    def partitions_by_dimension(self) -> Mapping[str, Partition]:
        return self.value


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


class CompositePartitionsDefinition(PartitionsDefinition):
    """The set of partitions is the cross product of partitions in the inner partitions
    definitions"""

    def __init__(self, partitions_defs: Mapping[str, PartitionsDefinition]):
        if not len(partitions_defs.keys()) == 2:
            raise DagsterInvalidInvocationError(
                "Dagster currently only supports composite partitions definitions with 2 partitions definitions. "
                f"Your composite partitions definition has {len(partitions_defs.keys())} partitions definitions."
            )
        check.mapping_param(
            partitions_defs, "partitions_defs", key_type=str, value_type=PartitionsDefinition
        )

        self._partitions_defs: List[PartitionDimensionDefinition] = sorted(
            [
                PartitionDimensionDefinition(name, partitions_def)
                for name, partitions_def in partitions_defs.items()
            ],
            key=lambda x: x.name,
        )

    @property
    def partitions_defs(self) -> Sequence[PartitionDimensionDefinition]:
        return self._partitions_defs

    def get_partitions(self, current_time: Optional[datetime] = None) -> Sequence[Partition]:
        partition_sequences = [
            partition_dim.partitions_def.get_partitions(current_time=current_time)
            for partition_dim in self._partitions_defs
        ]

        def get_multi_dimensional_partition(partitions_tuple: Tuple[Partition]):
            check.invariant(len(partitions_tuple) == len(self._partitions_defs))

            partitions_by_dimension: Dict[str, Partition] = {
                self._partitions_defs[i].name: partitions_tuple[i]
                for i in range(len(partitions_tuple))
            }

            return MultiDimensionalPartition(
                value=partitions_by_dimension,
                name=self.get_partition_key(
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
            isinstance(other, CompositePartitionsDefinition)
            and self.partitions_defs == other.partitions_defs
        )

    def __hash__(self):
        return hash(tuple(self.partitions_defs))

    def get_partition_key(
        self, partition_key_by_dimension: Union[Mapping[str, str], MultiDimensionalPartitionKey]
    ) -> str:
        if isinstance(partition_key_by_dimension, Mapping):
            check.mapping_param(
                partition_key_by_dimension,
                "partition_key_by_dimension",
                key_type=str,
                value_type=str,
            )
            partition_dim_names = set(
                [partition_dim.name for partition_dim in self._partitions_defs]
            )
            if set(partition_key_by_dimension.keys()) != partition_dim_names:
                extra_keys = set(partition_key_by_dimension.keys()) - partition_dim_names
                missing_keys = partition_dim_names - set(partition_key_by_dimension.keys())

                raise DagsterInvalidInvocationError(
                    "Invalid partition dimension keys provided. All provided keys must be defined as "
                    f"partition dimensions in the composite partitions. Valid keys are {partition_dim_names}. "
                    "You provided: \n"
                    f"{f'Extra keys: {extra_keys}.' if extra_keys else ''}"
                    f"{f'Missing keys {missing_keys}.' if missing_keys else ''}"
                )

            partition_key_by_dimension = (
                MultiDimensionalPartitionKey.from_partition_dimension_mapping(
                    partition_key_by_dimension
                )
            )

        else:
            check.inst_param(
                partition_key_by_dimension,
                "partition_key_by_dimension",
                MultiDimensionalPartitionKey,
            )

        return "|".join(
            [dim_key.partition_key for dim_key in partition_key_by_dimension.dimension_keys]
        )
