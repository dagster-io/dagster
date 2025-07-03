from typing import NamedTuple, Optional

from dagster._core.definitions.partitions.definition.partitions_definition import (
    PartitionsDefinition,
)
from dagster._core.definitions.partitions.subset.partitions_subset import PartitionsSubset
from dagster._serdes import whitelist_for_serdes


@whitelist_for_serdes
class SerializedPartitionsSubset(NamedTuple):
    serialized_subset: str
    serialized_partitions_def_unique_id: str
    serialized_partitions_def_class_name: str

    @classmethod
    def from_subset(cls, subset: PartitionsSubset, partitions_def: PartitionsDefinition):
        return cls(
            serialized_subset=subset.serialize(),
            serialized_partitions_def_unique_id=partitions_def.get_serializable_unique_identifier(),
            serialized_partitions_def_class_name=partitions_def.__class__.__name__,
        )

    def can_deserialize(self, partitions_def: Optional[PartitionsDefinition]) -> bool:
        if not partitions_def:
            # Asset had a partitions definition at storage time, but no longer does
            return False

        return partitions_def.can_deserialize_subset(
            self.serialized_subset,
            serialized_partitions_def_unique_id=self.serialized_partitions_def_unique_id,
            serialized_partitions_def_class_name=self.serialized_partitions_def_class_name,
        )

    def deserialize(self, partitions_def: PartitionsDefinition) -> PartitionsSubset:
        return partitions_def.deserialize_subset(self.serialized_subset)
