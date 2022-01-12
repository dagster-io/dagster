from abc import ABC, abstractmethod

from dagster.core.definitions.partition import PartitionsDefinition
from dagster.core.definitions.partition_key_range import PartitionKeyRange


class PartitionMapping(ABC):
    """Defines a correspondence between the partitions in an asset and the partitions in an asset
    that it depends on.
    """

    @abstractmethod
    def get_upstream_partitions_for_partition_range(
        self,
        downstream_partition_key_range: PartitionKeyRange,
        downstream_partitions_def: PartitionsDefinition,
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionKeyRange:
        """Returns the range of partition keys in the upstream asset that include data necessary
        to compute the contents of the given partition key range in the downstream asset.

        Args:
            downstream_partition_key_range (PartitionKeyRange): The range of partition keys in the
                downstream asset.
            downstream_partitions_def (PartitionsDefinition): The partitions definition for the
                downstream asset.
            upstream_partitions_def (PartitionsDefinition): The partitions definition for the
                upstream asset.
        """

    @abstractmethod
    def get_downstream_partitions_for_partition_range(
        self,
        upstream_partition_key_range: PartitionKeyRange,
        downstream_partitions_def: PartitionsDefinition,
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionKeyRange:
        """Returns the range of partition keys in the downstream asset that use the data in the given
        partition key range of the downstream asset.

        Args:
            upstream_partition_key_range (PartitionKeyRange): The range of partition keys in the
                upstream asset.
            downstream_partitions_def (PartitionsDefinition): The partitions definition for the
                downstream asset.
            upstream_partitions_def (PartitionsDefinition): The partitions definition for the
                upstream asset.
        """


class IdentityPartitionMapping(PartitionMapping):
    def get_upstream_partitions_for_partition_range(
        self,
        downstream_partition_key_range: PartitionKeyRange,
        downstream_partitions_def: PartitionsDefinition,  # pylint: disable=unused-argument
        upstream_partitions_def: PartitionsDefinition,  # pylint: disable=unused-argument
    ) -> PartitionKeyRange:
        return downstream_partition_key_range

    def get_downstream_partitions_for_partition_range(
        self,
        upstream_partition_key_range: PartitionKeyRange,
        downstream_partitions_def: PartitionsDefinition,  # pylint: disable=unused-argument
        upstream_partitions_def: PartitionsDefinition,  # pylint: disable=unused-argument
    ) -> PartitionKeyRange:
        return upstream_partition_key_range
