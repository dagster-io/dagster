from typing import List, Mapping, NamedTuple, Optional, Union

import dagster._check as check


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
    Representation of a single dimension of a multi-dimensional partition key.
    """

    def __new__(cls, dimension_name: str, partition_key: str):
        return super(PartitionDimensionKey, cls).__new__(
            cls,
            dimension_name=check.str_param(dimension_name, "dimension_name"),
            partition_key=check.str_param(partition_key, "partition_key"),
        )


class MultiDimensionalPartitionKey(str):
    """
    A multi-dimensional partition key stores the partition key for each dimension.
    Subclasses the string class to keep partition key type as a string.

    Contains additional methods to access the partition key for each dimension.
    Creates a string representation of the partition key for each dimension, separated by a pipe (|).
    Orders the dimensions by name, to ensure consistent string representation.
    """

    dimension_keys: List[PartitionDimensionKey] = []

    def __new__(cls, partition_dimension_mapping: Mapping[str, str]):
        check.mapping_param(
            partition_dimension_mapping, "partitions_by_dimension", key_type=str, value_type=str
        )

        dimension_keys: List[PartitionDimensionKey] = [
            PartitionDimensionKey(dimension, partition_dimension_mapping[dimension])
            for dimension in sorted(list(partition_dimension_mapping.keys()))
        ]

        str_key = super(MultiDimensionalPartitionKey, cls).__new__(
            cls, "|".join([dim_key.partition_key for dim_key in dimension_keys])
        )

        str_key.dimension_keys = dimension_keys

        return str_key

    def keys_by_dimension(self):
        return {dim_key.dimension_name: dim_key.partition_key for dim_key in self.dimension_keys}
