from typing import List, Mapping, NamedTuple

import dagster._check as check


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
