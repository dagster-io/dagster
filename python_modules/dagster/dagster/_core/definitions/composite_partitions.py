import itertools
from datetime import datetime
from typing import Optional, Sequence

from .partition import Partition, PartitionsDefinition


class CompositePartitionsDefinition(PartitionsDefinition):
    """The set of partitions is the cross product of partitions in the inner partitions
    definitions"""

    def __init__(self, partitions_defs: Sequence[PartitionsDefinition]):
        self._partitions_defs = partitions_defs

    @property
    def partitions_defs(self):
        return self._partitions_defs

    def get_partitions(self, current_time: Optional[datetime] = None) -> Sequence[Partition]:
        partition_sequences = [
            partitions_def.get_partitions(current_time=current_time)
            for partitions_def in self._partitions_defs
        ]
        return [
            Partition(
                value=tuple(partition.value for partition in partitions_tuple),
                name="|".join(partition.name for partition in partitions_tuple),
            )
            for partitions_tuple in itertools.product(*partition_sequences)
        ]

    def __eq__(self, other):
        return (
            isinstance(other, CompositePartitionsDefinition)
            and self.partitions_defs == other.partitions_defs
        )

    def __hash__(self):
        return hash(tuple(self.partitions_defs))
