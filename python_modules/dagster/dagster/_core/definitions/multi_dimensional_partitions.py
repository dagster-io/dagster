from typing import List, Mapping, NamedTuple, Optional, Sequence, Union

import dagster._check as check
from dagster._serdes import whitelist_for_serdes
from dagster._serdes.serdes import deserialize_as, serialize_dagster_namedtuple


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
        return deserialize_as(partition, MultiDimensionalPartitionKey)
    return partition
