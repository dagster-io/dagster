from abc import ABC, abstractmethod

from dagster.core.definitions.partition import PartitionsDefinition

from .partition_key_range import PartitionKeyRange


class PartitionMapping(ABC):
    """Defines a correspondence between the partitions in an asset and the partitions in an asset
    that it depends on.
    """

    @abstractmethod
    def get_parent_partitions_for_partition_range(
        self,
        child_partitions_def: PartitionsDefinition,
        parent_partitions_def: PartitionsDefinition,
        child_partition_key_range: PartitionKeyRange,
    ) -> PartitionKeyRange:
        """Returns the range of partition keys in the parent asset that include data necessary
        to compute the contents of the given partition key range in the child asset.

        Args:
            child_partitions_def (PartitionsDefinition): The partitions definition for the child
                asset.
            parent_partitions_def (PartitionsDefinition): The partitions definition for the parent
                asset.
            child_partition_key_range (PartitionKeyRange): The range of partition keys in the child
                asset.
        """

    @abstractmethod
    def get_child_partitions_for_partition_range(
        self,
        child_partitions_def: PartitionsDefinition,
        parent_partitions_def: PartitionsDefinition,
        parent_partition_key_range: PartitionKeyRange,
    ) -> PartitionKeyRange:
        """Returns the range of partition keys in the child asset that use the data in the given
        partition key range of the child asset.

        Args:
            child_partitions_def (PartitionsDefinition): The partitions definition for the child
                asset.
            parent_partitions_def (PartitionsDefinition): The partitions definition for the parent
                asset.
            parent_partition_key_range (PartitionKeyRange): The range of partition keys in the
                parent asset.
        """


class IdentityPartitionMapping(PartitionMapping):
    def get_parent_partitions_for_partition_range(
        self,
        child_partitions_def: PartitionsDefinition,  # pylint: disable=unused-argument
        parent_partitions_def: PartitionsDefinition,  # pylint: disable=unused-argument
        child_partition_key_range: PartitionKeyRange,
    ) -> PartitionKeyRange:
        return child_partition_key_range

    def get_child_partitions_for_partition_range(
        self,
        child_partitions_def: PartitionsDefinition,  # pylint: disable=unused-argument
        parent_partitions_def: PartitionsDefinition,  # pylint: disable=unused-argument
        parent_partition_key_range: PartitionKeyRange,
    ) -> PartitionKeyRange:
        return parent_partition_key_range
