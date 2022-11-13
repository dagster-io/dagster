from abc import ABC, abstractmethod
from typing import Optional

import dagster._check as check
from dagster._annotations import experimental, public
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.definitions.partition_key_range import PartitionKeyRange


@experimental
class PartitionMapping(ABC):
    """Defines a correspondence between the partitions in an asset and the partitions in an asset
    that it depends on.
    """

    @public
    @abstractmethod
    def get_upstream_partitions_for_partition_range(
        self,
        downstream_partition_key_range: Optional[PartitionKeyRange],
        downstream_partitions_def: Optional[PartitionsDefinition],
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

    @public
    @abstractmethod
    def get_downstream_partitions_for_partition_range(
        self,
        upstream_partition_key_range: PartitionKeyRange,
        downstream_partitions_def: Optional[PartitionsDefinition],
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


@experimental
class IdentityPartitionMapping(PartitionMapping):
    def get_upstream_partitions_for_partition_range(
        self,
        downstream_partition_key_range: Optional[PartitionKeyRange],
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionKeyRange:
        if downstream_partitions_def is None or downstream_partition_key_range is None:
            check.failed("downstream asset is not partitioned")

        return downstream_partition_key_range

    def get_downstream_partitions_for_partition_range(
        self,
        upstream_partition_key_range: PartitionKeyRange,
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionKeyRange:
        return upstream_partition_key_range


@experimental
class AllPartitionMapping(PartitionMapping):
    def get_upstream_partitions_for_partition_range(
        self,
        downstream_partition_key_range: Optional[PartitionKeyRange],
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionKeyRange:
        return PartitionKeyRange(
            upstream_partitions_def.get_first_partition_key(),
            upstream_partitions_def.get_last_partition_key(),
        )

    def get_downstream_partitions_for_partition_range(
        self,
        upstream_partition_key_range: PartitionKeyRange,
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionKeyRange:
        raise NotImplementedError()


@experimental
class LastPartitionMapping(PartitionMapping):
    def get_upstream_partitions_for_partition_range(
        self,
        downstream_partition_key_range: Optional[PartitionKeyRange],
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionKeyRange:
        last_partition_key = upstream_partitions_def.get_last_partition_key()
        return PartitionKeyRange(last_partition_key, last_partition_key)

    def get_downstream_partitions_for_partition_range(
        self,
        upstream_partition_key_range: PartitionKeyRange,
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionKeyRange:
        raise NotImplementedError()


def infer_partition_mapping(
    partition_mapping: Optional[PartitionMapping], partitions_def: Optional[PartitionsDefinition]
) -> PartitionMapping:
    if partition_mapping is not None:
        return partition_mapping
    elif partitions_def is not None:
        return partitions_def.get_default_partition_mapping()
    else:
        return AllPartitionMapping()
