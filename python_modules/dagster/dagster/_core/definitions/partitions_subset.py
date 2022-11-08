import json
from typing import Iterable

from .partition import PartitionsDefinition


class PartitionsSubset:
    """Represents a subset of the partitions within a PartitionsDefinition"""

    def __init__(self, partitions_def: PartitionsDefinition, subset=None):
        self._partitions_def = partitions_def
        self._subset = subset or set()

    def get_partition_keys_not_in_subset(self) -> Iterable[str]:
        return set(self._partitions_def.get_partition_keys()) - self._subset

    def with_partition_keys(self, partition_keys: Iterable[str]) -> "PartitionsSubset":
        return PartitionsSubset(self._partitions_def, self._subset | set(partition_keys))

    def serialize(self) -> str:
        return json.dumps(self._subset)

    @classmethod
    def from_serialized(
        self, serialized: str, partitions_def: PartitionsDefinition
    ) -> "PartitionsSubset":
        return PartitionsSubset(subset=json.loads(serialized), partitions_def=partitions_def)
