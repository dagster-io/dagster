import itertools
from datetime import datetime
from typing import NamedTuple, Optional, Sequence, Mapping, TypeVar, Tuple, cast
import dagster._check as check
from .partition import Partition, PartitionsDefinition


class MultiDimensionalPartition(Partition):
    def __init__(self, value: Mapping[str, Partition], name: Optional[str] = None):
        self._value = check.mapping_param(value, "value", key_type=str, value_type=Partition)
        self._name = cast(str, check.opt_str_param(name, "name", str(value)))

    @property
    def value(self) -> Mapping[str, Partition]:
        return self._value

    @property
    def name(self) -> str:
        return self._name

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, MultiDimensionalPartition)
            and self.value == other.value
            and self.name == other.name
        )


class PartitionDimensionDefinition(
    NamedTuple(
        "_PartitionDimensionDefinition",
        [
            ("name", str),
            ("partitions_def", PartitionsDefinition),
        ],
    )
):
    def __new__(
        cls,
        name: str,
        partitions_def: PartitionsDefinition,
    ):
        return super().__new__(
            cls,
            name=check.str_param(name, "name"),
            partitions_def=check.inst_param(partitions_def, "partitions_def", PartitionsDefinition),
        )


class CompositePartitionsDefinition(PartitionsDefinition):
    """The set of partitions is the cross product of partitions in the inner partitions
    definitions"""

    def __init__(self, partitions_defs: Mapping[str, PartitionsDefinition]):
        if not len(partitions_defs.keys()) == 2:
            raise DagsterInvalidInvocationError(
                "Dagster currently only supports composite partitions definitions with 2 partitions definitions. "
                f"Your composite partitions definition has {len(partitions_defs.keys())} partitions definitions."
            )
        check.mapping_param(
            partitions_defs, "partitions_defs", key_type=str, value_type=PartitionsDefinition
        )

        self._partitions_defs: List[PartitionDimensionDefinition] = [
            PartitionDimensionDefinition(name, partitions_def)
            for name, partitions_def in partitions_defs.items()
        ]

    @property
    def partitions_defs(self) -> Sequence[PartitionDimensionDefinition]:
        return self._partitions_defs

    def get_partitions(self, current_time: Optional[datetime] = None) -> Sequence[Partition]:
        partition_sequences = [
            partition_dim.partitions_def.get_partitions(current_time=current_time)
            for partition_dim in self._partitions_defs
        ]

        def get_multi_dimensional_partition(partitions_tuple: Tuple[Partition]):
            check.invariant(len(partitions_tuple) == len(self._partitions_defs))
            return MultiDimensionalPartition(
                value={
                    self._partitions_defs[i].name: partitions_tuple[i]
                    for i in range(len(partitions_tuple))
                },
                name="|".join([str(partition.name) for partition in partitions_tuple]),
            )

        return [
            get_multi_dimensional_partition(partitions_tuple)
            for partitions_tuple in itertools.product(*partition_sequences)
        ]

    def __eq__(self, other):
        return (
            isinstance(other, CompositePartitionsDefinition)
            and self.partitions_defs == other.partitions_defs
        )

    def __hash__(self):
        return hash(tuple(self.partitions_defs))
