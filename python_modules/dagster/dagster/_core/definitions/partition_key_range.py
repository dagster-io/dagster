from typing import NamedTuple

from dagster._annotations import PublicAttr


class PartitionKeyRange(NamedTuple):
    """Defines a range of partitions.

    Attributes:
        start (str): The starting partition key in the range (inclusive).
        end (str): The ending partition key in the range (inclusive).

    Examples:
        .. code-block:: python

            partitions_def = StaticPartitionsDefinition(["a", "b", "c", "d"])
            partition_key_range = PartitionKeyRange(start="a", end="c") # Represents ["a", "b", "c"]
    """

    # Inclusive on both sides
    start: PublicAttr[str]
    end: PublicAttr[str]
