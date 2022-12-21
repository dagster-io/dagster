from abc import ABC, abstractmethod
from typing import NamedTuple, Optional

import dagster._check as check
from dagster._annotations import public
from dagster._core.definitions.partition import PartitionsDefinition, PartitionsSubset
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._serdes import whitelist_for_serdes


class PartitionMapping(ABC):
    """Defines a correspondence between the partitions in an asset and the partitions in an asset
    that it depends on.

    Overriding PartitionMapping outside of Dagster is not supported. The abstract methods of this
    class may change at any time.
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
        partition key range of the upstream asset.

        Args:
            upstream_partition_key_range (PartitionKeyRange): The range of partition keys in the
                upstream asset.
            downstream_partitions_def (PartitionsDefinition): The partitions definition for the
                downstream asset.
            upstream_partitions_def (PartitionsDefinition): The partitions definition for the
                upstream asset.
        """

    @public
    def get_upstream_partitions_for_partitions(
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionsSubset:
        """
        Returns the subset of partition keys in the upstream asset that include data necessary
        to compute the contents of the given partition key subset in the downstream asset.

        Args:
            downstream_partitions_subset (Optional[PartitionsSubset]):
                The subset of partition keys in the downstream asset.
            upstream_partitions_def (PartitionsDefinition): The partitions definition for the
                upstream asset.
        """
        upstream_key_ranges = []
        if downstream_partitions_subset is None:
            upstream_key_ranges.append(
                self.get_upstream_partitions_for_partition_range(
                    None, None, upstream_partitions_def
                )
            )
        else:
            for key_range in downstream_partitions_subset.get_partition_key_ranges():
                upstream_key_ranges.append(
                    self.get_upstream_partitions_for_partition_range(
                        key_range,
                        downstream_partitions_subset.partitions_def,
                        upstream_partitions_def,
                    )
                )

        return upstream_partitions_def.empty_subset().with_partition_keys(
            pk
            for upstream_key_range in upstream_key_ranges
            for pk in upstream_partitions_def.get_partition_keys_in_range(upstream_key_range)
        )

    @public
    def get_downstream_partitions_for_partitions(
        self,
        upstream_partitions_subset: PartitionsSubset,
        downstream_partitions_def: PartitionsDefinition,
    ) -> PartitionsSubset:
        """
        Returns the subset of partition keys in the downstream asset that use the data in the given
        partition key subset of the upstream asset.

        Args:
            upstream_partitions_subset (Union[PartitionKeyRange, PartitionsSubset]): The
                subset of partition keys in the upstream asset.
            downstream_partitions_def (PartitionsDefinition): The partitions definition for the
                downstream asset.
        """
        downstream_key_ranges = []
        for key_range in upstream_partitions_subset.get_partition_key_ranges():
            downstream_key_ranges.append(
                self.get_downstream_partitions_for_partition_range(
                    key_range,
                    downstream_partitions_def,
                    upstream_partitions_subset.partitions_def,
                )
            )

        return downstream_partitions_def.empty_subset().with_partition_keys(
            pk
            for upstream_key_range in downstream_key_ranges
            for pk in downstream_partitions_def.get_partition_keys_in_range(upstream_key_range)
        )


@whitelist_for_serdes
class IdentityPartitionMapping(PartitionMapping, NamedTuple("_IdentityPartitionMapping", [])):
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


@whitelist_for_serdes
class AllPartitionMapping(PartitionMapping, NamedTuple("_AllPartitionMapping", [])):
    def get_upstream_partitions_for_partitions(
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionsSubset:
        first = upstream_partitions_def.get_first_partition_key()
        last = upstream_partitions_def.get_last_partition_key()

        empty_subset = upstream_partitions_def.empty_subset()
        if first is not None and last is not None:
            return empty_subset.with_partition_key_range(PartitionKeyRange(first, last))
        else:
            return empty_subset

    def get_upstream_partitions_for_partition_range(
        self,
        downstream_partition_key_range: Optional[PartitionKeyRange],
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionKeyRange:
        raise NotImplementedError()

    def get_downstream_partitions_for_partition_range(
        self,
        upstream_partition_key_range: PartitionKeyRange,
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionKeyRange:
        raise NotImplementedError()


@whitelist_for_serdes
class LastPartitionMapping(PartitionMapping, NamedTuple("_LastPartitionMapping", [])):
    def get_upstream_partitions_for_partitions(
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionsSubset:
        last = upstream_partitions_def.get_last_partition_key()

        empty_subset = upstream_partitions_def.empty_subset()
        if last is not None:
            return empty_subset.with_partition_keys([last])
        else:
            return empty_subset

    def get_upstream_partitions_for_partition_range(
        self,
        downstream_partition_key_range: Optional[PartitionKeyRange],
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionKeyRange:
        raise NotImplementedError()

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


def get_builtin_partition_mapping_types():
    from dagster._core.definitions.time_window_partition_mapping import TimeWindowPartitionMapping

    return (
        AllPartitionMapping,
        IdentityPartitionMapping,
        LastPartitionMapping,
        TimeWindowPartitionMapping,
    )
