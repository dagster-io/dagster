from datetime import datetime
from typing import NamedTuple, Optional, Sequence, cast

import dagster._check as check
from dagster._annotations import PublicAttr
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
class TimeWindowPartitionMapping(
    PartitionMapping,
    NamedTuple(
        "_TimeWindowPartitionMapping",
        [("start_offset", PublicAttr[int]), ("end_offset", PublicAttr[int])],
    ),
):
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

    Attributes:
        start_offset (int): If not 0, then the starts of the upstream windows are shifted by this
            offset relative to the starts of the downstream windows. For example, if start_offset=-1
            and end_offset=0, then the downstream partition "2022-07-04" would map to the upstream
            partitions "2022-07-03" and "2022-07-04". Only permitted to be non-zero when the
            upstream and downstream PartitionsDefinitions are the same. Defaults to 0.
        end_offset (int): If not 0, then the ends of the upstream windows are shifted by this
            offset relative to the ends of the downstream windows. For example, if start_offset=0
            and end_offset=1, then the downstream partition "2022-07-04" would map to the upstream
            partitions "2022-07-04" and "2022-07-05". Only permitted to be non-zero when the
            upstream and downstream PartitionsDefinitions are the same. Defaults to 0.

    Examples:
        .. code-block:: python

            from dagster import DailyPartitionsDefinition, TimeWindowPartitionMapping, AssetIn, asset

            partitions_def = DailyPartitionsDefinition(start_date="2020-01-01")

            @asset(partitions_def=partitions_def)
            def asset1():
                ...

            @asset(
                partitions_def=partitions_def,
                ins={
                    "asset1": AssetIn(
                        partition_mapping=TimeWindowPartitionMapping(start_offset=-1)
                    )
                }
            )
            def asset2(asset1):
                ...
    """

    def __new__(cls, start_offset: int = 0, end_offset: int = 0):
        return super(TimeWindowPartitionMapping, cls).__new__(
            cls,
            start_offset=check.int_param(start_offset, "start_offset"),
            end_offset=check.int_param(end_offset, "end_offset"),
        )

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
            self.start_offset,
            self.end_offset,
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
            -self.start_offset,
            -self.end_offset,
        )

    def _map_partitions(
        self,
        from_partitions_def: PartitionsDefinition,
        to_partitions_def: PartitionsDefinition,
        from_partition_time_windows: Sequence[TimeWindow],
        start_offset: int,
        end_offset: int,
    ) -> PartitionsSubset:
        if not isinstance(from_partitions_def, TimeWindowPartitionsDefinition) or not isinstance(
            to_partitions_def, TimeWindowPartitionsDefinition
        ):
            raise DagsterInvalidDefinitionError(
                "TimeWindowPartitionMappings can only operate on TimeWindowPartitionsDefinitions"
            )

        # mypy requires this for some reason
        from_partitions_def = cast(TimeWindowPartitionsDefinition, from_partitions_def)
        to_partitions_def = cast(TimeWindowPartitionsDefinition, to_partitions_def)

        if start_offset != 0 or end_offset != 0:
            check.invariant(from_partitions_def.cron_schedule == to_partitions_def.cron_schedule)

        if to_partitions_def.timezone != from_partitions_def.timezone:
            raise DagsterInvalidDefinitionError("Timezones don't match")

        time_windows = []
        for from_partition_time_window in from_partition_time_windows:
            from_start_dt, from_end_dt = from_partition_time_window
            offsetted_start_dt = _offsetted_datetime(
                from_partitions_def, from_start_dt, start_offset
            )
            offsetted_end_dt = _offsetted_datetime(from_partitions_def, from_end_dt, end_offset)

            to_start_partition_key = (
                to_partitions_def.get_partition_key_for_timestamp(
                    offsetted_start_dt.timestamp(), end_closed=False
                )
                if offsetted_start_dt is not None
                else None
            )
            to_end_partition_key = (
                to_partitions_def.get_partition_key_for_timestamp(
                    offsetted_end_dt.timestamp(), end_closed=True
                )
                if offsetted_end_dt is not None
                else None
            )

            if to_start_partition_key is not None or to_end_partition_key is not None:
                window_start = (
                    to_partitions_def.start_time_for_partition_key(to_start_partition_key)
                    if to_start_partition_key
                    else cast(TimeWindow, to_partitions_def.get_first_partition_window()).start
                )
                window_end = (
                    to_partitions_def.end_time_for_partition_key(to_end_partition_key)
                    if to_end_partition_key
                    else cast(TimeWindow, to_partitions_def.get_last_partition_window()).end
                )

                time_windows.append(TimeWindow(window_start, window_end))

        return TimeWindowPartitionsSubset(
            to_partitions_def,
            time_windows,
            num_partitions=sum(
                len(to_partitions_def.get_partition_keys_in_time_window(time_window))
                for time_window in time_windows
            ),
        )


def _offsetted_datetime(
    partitions_def: TimeWindowPartitionsDefinition, dt: datetime, offset: int
) -> Optional[datetime]:
    for _ in range(abs(offset)):
        if offset < 0:
            prev_window = partitions_def.get_prev_partition_window(dt)
            if prev_window is None:
                return None

            dt = prev_window.start
        else:
            # TODO: what if we're at the end of the line?
            next_window = partitions_def.get_next_partition_window(dt)
            if next_window is None:
                return None

            dt = next_window.end

    return dt
