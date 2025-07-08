from collections.abc import Sequence
from typing import Optional

from dagster._core.instance import DagsterInstance, DynamicPartitionsStore
from dagster._core.types.pagination import PaginatedResults
from dagster._utils.cached_method import cached_method


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
