from typing import Sequence

from dagster._annotations import public
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.definitions.partition_key_range import PartitionKeyRange


class BackfillStrategyContext:
    def __init__(self, partition_key_ranges):
        self._partition_key_ranges = partition_key_ranges

    @public  # type: ignore
    @property
    def partition_key_ranges(self) -> Sequence[PartitionKeyRange]:
        return self._partition_key_ranges

    @public  # type: ignore
    @property
    def partitions_def(self) -> PartitionsDefinition:
        return self._partition_key_ranges
