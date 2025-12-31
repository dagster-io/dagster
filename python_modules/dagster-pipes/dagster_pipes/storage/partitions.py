"""Partition specification types for storage adapters."""

from dataclasses import dataclass
from datetime import datetime
from typing import Union


@dataclass(frozen=True)
class PartitionKeys:
    """Discrete partition key(s) to load or store.

    For single partition: PartitionKeys.single("2024-01-15")
    For multiple partitions: PartitionKeys(keys=("2024-01-15", "2024-01-16"))
    """

    keys: tuple[str, ...]

    @classmethod
    def single(cls, key: str) -> "PartitionKeys":
        """Create a PartitionKeys for a single partition."""
        return cls(keys=(key,))

    @classmethod
    def multiple(cls, keys: list[str]) -> "PartitionKeys":
        """Create a PartitionKeys for multiple partitions."""
        return cls(keys=tuple(keys))


@dataclass(frozen=True)
class PartitionKeyRange:
    """Range of partition keys (both start and end inclusive).

    Used for string-based partition ranges, e.g.:
        PartitionKeyRange(start="2024-01-01", end="2024-01-31")
    """

    start: str
    end: str


@dataclass(frozen=True)
class TimeWindowRange:
    """Time-based partition range.

    Start is inclusive, end is exclusive (following Dagster convention).

    Example:
        TimeWindowRange(
            start=datetime(2024, 1, 1),
            end=datetime(2024, 2, 1)
        )
    """

    start: datetime
    end: datetime


# Union type for all partition specifications
PartitionSpec = Union[PartitionKeys, PartitionKeyRange, TimeWindowRange, None]
