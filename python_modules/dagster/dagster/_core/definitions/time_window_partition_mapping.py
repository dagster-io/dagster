from typing import Optional, cast

import dagster._check as check
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.partition_mapping import PartitionMapping
from dagster._core.definitions.time_window_partitions import TimeWindowPartitionsDefinition
from dagster._core.errors import DagsterInvalidDefinitionError


class TimeWindowPartitionMapping(PartitionMapping):
    """
    The default mapping between two TimeWindowPartitionsDefinitions.

    A partition in the downstream partitions definition is mapped to all partitions in the upstream
    asset whose time windows overlap it.

    This means that, if the upstream and downstream partitions definitions share the same time
    period, then this mapping is essentially the identity partition mapping - plus conversion of
    datetime formats.

    If the upstream time period is coarser than the downstream time period, then each partition in
    the downstream asset will map to a single (larger) upstream partition. E.g. if the downstream is
    hourly and the upstream is daily, then each hourly partition in the downstream will map to the
    daily partition in the upstream that contains that hour.

    If the upstream time period is finer than the downstream time period, then each partition in the
    downstream asset will map to multiple upstream partitions. E.g. if the downstream is daily and
    the upstream is hourly, then each daily partition in the downstream asset will map to the 24
    hourly partitions in the upstream that occur on that day.
    """

    def get_upstream_partitions_for_partition_range(
        self,
        downstream_partition_key_range: Optional[PartitionKeyRange],
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionKeyRange:
        if downstream_partitions_def is None or downstream_partition_key_range is None:
            check.failed("downstream asset is not partitioned")

        return self._map_partitions(
            downstream_partitions_def, upstream_partitions_def, downstream_partition_key_range
        )

    def get_downstream_partitions_for_partition_range(
        self,
        upstream_partition_key_range: PartitionKeyRange,
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionKeyRange:
        if downstream_partitions_def is None:
            check.failed("downstream asset is not partitioned")

        return self._map_partitions(
            upstream_partitions_def, downstream_partitions_def, upstream_partition_key_range
        )

    def _map_partitions(
        self,
        from_partitions_def: PartitionsDefinition,
        to_partitions_def: PartitionsDefinition,
        from_partition_key_range: PartitionKeyRange,
    ) -> PartitionKeyRange:
        if not isinstance(from_partitions_def, TimeWindowPartitionsDefinition) or not isinstance(
            from_partitions_def, TimeWindowPartitionsDefinition
        ):
            raise DagsterInvalidDefinitionError(
                "TimeWindowPartitionMappings can only operate on TimeWindowPartitionsDefinitions"
            )
        from_partitions_def = cast(TimeWindowPartitionsDefinition, from_partitions_def)
        to_partitions_def = cast(TimeWindowPartitionsDefinition, to_partitions_def)

        if to_partitions_def.timezone != from_partitions_def.timezone:
            raise DagsterInvalidDefinitionError("Timezones don't match")

        from_start_dt = from_partitions_def.start_time_for_partition_key(
            from_partition_key_range.start
        )
        from_end_dt = from_partitions_def.end_time_for_partition_key(from_partition_key_range.end)

        to_start_partition_key = to_partitions_def.get_partition_key_for_timestamp(
            from_start_dt.timestamp(), end_closed=False
        )
        to_end_partition_key = to_partitions_def.get_partition_key_for_timestamp(
            from_end_dt.timestamp(), end_closed=True
        )

        return PartitionKeyRange(to_start_partition_key, to_end_partition_key)
