import hashlib
import json
from collections import defaultdict
from collections.abc import Sequence
from typing import Optional

from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.instance import DagsterInstance, DynamicPartitionsStore
from dagster._core.types.pagination import PaginatedResults
from dagster._utils.cached_method import cached_method

# In the Dagster UI users can select partition ranges following the format '2022-01-13...2022-01-14'
# "..." is an invalid substring in partition keys
# The other escape characters are characters that may not display in the Dagster UI.
INVALID_PARTITION_SUBSTRINGS = ["...", "\a", "\b", "\f", "\n", "\r", "\t", "\v", "\0"]


def raise_error_on_invalid_partition_key_substring(partition_keys: Sequence[str]) -> None:
    for partition_key in partition_keys:
        found_invalid_substrs = [
            invalid_substr
            for invalid_substr in INVALID_PARTITION_SUBSTRINGS
            if invalid_substr in partition_key
        ]
        if found_invalid_substrs:
            raise DagsterInvalidDefinitionError(
                f"{found_invalid_substrs} are invalid substrings in a partition key"
            )


def raise_error_on_duplicate_partition_keys(partition_keys: Sequence[str]) -> None:
    counts: dict[str, int] = defaultdict(lambda: 0)
    for partition_key in partition_keys:
        counts[partition_key] += 1
    found_duplicates = [key for key in counts.keys() if counts[key] > 1]
    if found_duplicates:
        raise DagsterInvalidDefinitionError(
            "Partition keys must be unique. Duplicate instances of partition keys:"
            f" {found_duplicates}."
        )


class CachingDynamicPartitionsLoader(DynamicPartitionsStore):
    """A batch loader that caches the partition keys for a given dynamic partitions definition,
    to avoid repeated calls to the database for the same partitions definition.
    """

    def __init__(self, instance: DagsterInstance):
        self._instance = instance

    @cached_method
    def get_dynamic_partitions(self, partitions_def_name: str) -> Sequence[str]:
        return self._instance.get_dynamic_partitions(partitions_def_name)

    @cached_method
    def get_paginated_dynamic_partitions(
        self, partitions_def_name: str, limit: int, ascending: bool, cursor: Optional[str] = None
    ) -> PaginatedResults[str]:
        return self._instance.get_paginated_dynamic_partitions(
            partitions_def_name=partitions_def_name, limit=limit, ascending=ascending, cursor=cursor
        )

    @cached_method
    def has_dynamic_partition(self, partitions_def_name: str, partition_key: str) -> bool:
        return self._instance.has_dynamic_partition(partitions_def_name, partition_key)


def generate_partition_key_based_definition_id(partition_keys: Sequence[str]) -> str:
    return hashlib.sha1(json.dumps(partition_keys).encode("utf-8")).hexdigest()
