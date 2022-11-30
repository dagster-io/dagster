from abc import ABC, abstractmethod
from typing import Optional, cast, Union

import dagster._check as check
from dagster._annotations import experimental, public
from dagster._core.definitions.partition import (
    PartitionsDefinition,
    DefaultPartitionsSubset,
    PartitionsSubset,
)
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.multi_dimensional_partitions import (
    MultiPartitionsDefinition,
    MultiPartitionKey,
)


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
    ) -> Union[PartitionKeyRange, PartitionsSubset]:
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
    ) -> Union[PartitionKeyRange, PartitionsSubset]:
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


@experimental
class SingleDimensionToMultiPartitionMapping(PartitionMapping):
    """
    Defines a correspondence between an upstream single-dimensional partitions definition
    and a downstream MultiPartitionsDefinition. The upstream partitions definition must be
    a dimension of the downstream MultiPartitionsDefinition.

    Args:
        partition_dimension_name (str): The name of the partition dimension in the downstream
            MultiPartitionsDefinition that matches the upstream partitions definition.
    """

    def __init__(self, partition_dimension_name: str):
        self.partition_dimension_name = partition_dimension_name

    def get_upstream_partitions_for_partition_range(
        self,
        downstream_partition_key_range: Optional[PartitionKeyRange],
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionKeyRange:
        if downstream_partitions_def is None or downstream_partition_key_range is None:
            check.failed("downstream asset is not partitioned")

        if not isinstance(downstream_partitions_def, MultiPartitionsDefinition):
            check.failed("downstream asset is not multi-partitioned")
        if not (
            isinstance(downstream_partition_key_range.start, MultiPartitionKey)
            and isinstance(downstream_partition_key_range.end, MultiPartitionKey)
        ):
            check.failed(
                "Start and end fields of downstream partition key range must be MultiPartitionKeys"
            )

        matching_dimensions = [
            partitions_def
            for partitions_def in downstream_partitions_def.partitions_defs
            if partitions_def.name == self.partition_dimension_name
        ]
        if len(matching_dimensions) != 1:
            check.failed(f"Partition dimension '{self.partition_dimension_name}' not found")
        matching_dimension_def = next(iter(matching_dimensions))

        if upstream_partitions_def != matching_dimension_def.partitions_def:
            check.failed(
                "The upstream partitions definition does not have the same partitions definition "
                f"as dimension {matching_dimension_def.name}"
            )

        range_start = cast(MultiPartitionKey, downstream_partition_key_range.start)
        range_end = cast(MultiPartitionKey, downstream_partition_key_range.end)
        return PartitionKeyRange(
            range_start.keys_by_dimension[self.partition_dimension_name],
            range_end.keys_by_dimension[self.partition_dimension_name],
        )

    def get_downstream_partitions_for_partition_range(
        self,
        upstream_partition_key_range: PartitionKeyRange,
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionsSubset:
        if downstream_partitions_def is None or not isinstance(
            downstream_partitions_def, MultiPartitionsDefinition
        ):
            check.failed("downstream asset is not multi-partitioned")

        matching_dimensions = [
            partitions_def
            for partitions_def in downstream_partitions_def.partitions_defs
            if partitions_def.name == self.partition_dimension_name
        ]
        if len(matching_dimensions) != 1:
            check.failed(f"Partition dimension '{self.partition_dimension_name}' not found")
        matching_dimension_def = next(iter(matching_dimensions))

        if upstream_partitions_def != matching_dimension_def.partitions_def:
            check.failed(
                "The upstream partitions definition does not have the same partitions definition "
                f"as dimension {matching_dimension_def.name}"
            )

        dimension_partition_keys = matching_dimension_def.partitions_def.get_partition_keys()
        check.invariant(
            upstream_partition_key_range.start in dimension_partition_keys
            and upstream_partition_key_range.end in dimension_partition_keys,
            f"Invalid upstream partition key range provided. The range must be a subset of the partition keys of the downstream {self.partition_dimension_name} dimension.",
        )
        range_keys = dimension_partition_keys[
            dimension_partition_keys.index(
                upstream_partition_key_range.start
            ) : dimension_partition_keys.index(upstream_partition_key_range.end)
        ]

        matching_keys = []
        for key in downstream_partitions_def.get_partition_keys():
            key = cast(MultiPartitionKey, key)
            if key.keys_by_dimension[self.partition_dimension_name] in range_keys:
                matching_keys.append(key)

        return DefaultPartitionsSubset(downstream_partitions_def, set(matching_keys))


def infer_partition_mapping(
    partition_mapping: Optional[PartitionMapping], partitions_def: Optional[PartitionsDefinition]
) -> PartitionMapping:
    if partition_mapping is not None:
        return partition_mapping
    elif partitions_def is not None:
        return partitions_def.get_default_partition_mapping()
    else:
        return AllPartitionMapping()
