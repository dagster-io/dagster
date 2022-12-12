from typing import NamedTuple, Optional, Sequence, cast

import dagster._check as check
from dagster._core.definitions.partition import PartitionsDefinition, PartitionsSubset
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.partition_mapping import PartitionMapping
from dagster._core.definitions.time_window_partitions import (
    TimeWindow,
    TimeWindowPartitionsDefinition,
    TimeWindowPartitionsSubset,
)
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._serdes import whitelist_for_serdes


@whitelist_for_serdes
class TimeWindowPartitionMapping(PartitionMapping, NamedTuple("_TimeWindowPartitionMapping", [])):
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
        raise NotImplementedError()

    def get_upstream_partitions_for_partitions(
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionsSubset:
        if not isinstance(downstream_partitions_subset, TimeWindowPartitionsSubset):
            check.failed("downstream_partitions_subset must be a TimeWindowPartitionsSubset")

        return self._map_partitions(
            downstream_partitions_subset.partitions_def,
            upstream_partitions_def,
            downstream_partitions_subset.included_time_windows,
        )

    def get_downstream_partitions_for_partition_range(
        self,
        upstream_partition_key_range: PartitionKeyRange,
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
    ) -> PartitionKeyRange:
        raise NotImplementedError()

    def get_downstream_partitions_for_partitions(
        self,
        upstream_partitions_subset: PartitionsSubset,
        downstream_partitions_def: Optional[PartitionsDefinition],
    ) -> PartitionsSubset:
        if not isinstance(downstream_partitions_def, TimeWindowPartitionsDefinition):
            check.failed("downstream_partitions_def must be a TimeWindowPartitionsDefinitions")

        if not isinstance(upstream_partitions_subset, TimeWindowPartitionsSubset):
            check.failed("upstream_partitions_subset must be a TimeWindowPartitionsSubset")

        return self._map_partitions(
            upstream_partitions_subset.partitions_def,
            downstream_partitions_def,
            upstream_partitions_subset.included_time_windows,
        )

    def _map_partitions(
        self,
        from_partitions_def: PartitionsDefinition,
        to_partitions_def: PartitionsDefinition,
        from_partition_time_windows: Sequence[TimeWindow],
    ) -> PartitionsSubset:
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

        time_windows = []
        for from_partition_time_window in from_partition_time_windows:
            from_start_dt, from_end_dt = from_partition_time_window

            to_start_partition_key = to_partitions_def.get_partition_key_for_timestamp(
                from_start_dt.timestamp(), end_closed=False
            )
            to_end_partition_key = to_partitions_def.get_partition_key_for_timestamp(
                from_end_dt.timestamp(), end_closed=True
            )
            time_windows.append(
                TimeWindow(
                    to_partitions_def.start_time_for_partition_key(to_start_partition_key),
                    to_partitions_def.end_time_for_partition_key(to_end_partition_key),
                )
            )

        return TimeWindowPartitionsSubset(
            to_partitions_def,
            time_windows,
        )
