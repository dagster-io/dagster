from datetime import datetime, timedelta
from typing import cast

from dagster import check
from dagster.core.definitions.partition import PartitionsDefinition, ScheduleType
from dagster.core.definitions.time_window_partitions import TimeWindowPartitionsDefinition
from dagster.core.errors import DagsterInvalidDefinitionError

from .partition_key_range import PartitionKeyRange
from .partition_mapping import PartitionMapping


class TimeWindowPartitionMapping(PartitionMapping):
    """
    The default mapping between two TimeWindowPartitionsDefinitions.

    A partition in the child partitions definition is mapped to all partitions in the parent whose
    time windows overlap it.

    This means that, if the parent and child partitions definitions share the same time period, then
    this mapping is essentially the identity partition mapping - plus conversion of datetime formats.

    If the parent time period is coarser than the child time period, then each partition in the child
    will map to a single (larger) parent partition. E.g. if the child is hourly and the parent is
    daily, then each hourly partition in the child will map to the daily partition in the parent
    that contains that hour.

    If the parent time period is finer than the child time period, then each partition in the child
    will map to multiple parent partitions. E.g. if the child is daily and the parent is hourly,
    then each daily partition in the child will map to the 24 hourly partitions in the parent that
    occur on that day.
    """

    def get_parent_partitions(
        self,
        child_partitions_def: PartitionsDefinition,
        parent_partitions_def: PartitionsDefinition,
        child_partition_key_range: PartitionKeyRange,
    ) -> PartitionKeyRange:
        return self._map_partitions(
            child_partitions_def, parent_partitions_def, child_partition_key_range
        )

    def get_child_partitions(
        self,
        child_partitions_def: PartitionsDefinition,
        parent_partitions_def: PartitionsDefinition,
        parent_partition_key_range: PartitionKeyRange,
    ) -> PartitionKeyRange:
        return self._map_partitions(
            parent_partitions_def, child_partitions_def, parent_partition_key_range
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

        to_period = to_partitions_def.schedule_type
        from_period = from_partitions_def.schedule_type

        from_start_dt = datetime.strptime(from_partition_key_range.start, from_partitions_def.fmt)
        from_end_dt = datetime.strptime(from_partition_key_range.end, from_partitions_def.fmt)

        if to_period > from_period:
            to_start_dt = round_datetime_to_period(from_start_dt, to_period)
            to_end_dt = round_datetime_to_period(from_end_dt, to_period)
        elif to_period < from_period:
            to_start_dt = from_start_dt
            # TODO: daylight savings
            to_end_dt = (from_end_dt + from_period.delta) - to_period.delta
        else:
            to_start_dt = from_start_dt
            to_end_dt = from_end_dt

        return PartitionKeyRange(
            to_start_dt.strftime(to_partitions_def.fmt),
            to_end_dt.strftime(to_partitions_def.fmt),
        )


class RollingWindowTimeWindowPartitionMapping(PartitionMapping):
    """
    Partition N in a child asset depends on the partitions in the inclusive range [N - start_offset,
    N - end_offset in the parent asset].

    For example, if the assets have a daily partitioning, and start_offset and end_offset are both
    1, then partition 2021-12-06 in the child asset would map to 2021-12-05 in the parent asset.
    """

    start_offset: int
    end_offset: int

    def get_parent_partitions(
        self,
        child_partitions_def: PartitionsDefinition,
        parent_partitions_def: PartitionsDefinition,
        child_partition_key_range: PartitionKeyRange,
    ) -> PartitionKeyRange:
        assert child_partitions_def.schedule_type == parent_partitions_def.schedule_type
        return self._shift_partition_key_range(
            child_partitions_def, child_partition_key_range, -self.start_offset, -self.end_offset
        )

    def get_child_partitions(
        self,
        child_partitions_def: PartitionsDefinition,
        parent_partitions_def: PartitionsDefinition,
        parent_partition_key_range: PartitionKeyRange,
    ) -> PartitionKeyRange:
        assert child_partitions_def.schedule_type == parent_partitions_def.schedule_type
        return self._shift_partition_key_range(
            child_partitions_def, parent_partition_key_range, self.start_offset, self.end_offset
        )

    def _shift_partition_key_range(
        self, partitions_def, partition_key_range, start_shift, end_shift
    ):
        child_start_dt = datetime.strptime(partition_key_range.start, partitions_def.fmt)
        child_end_dt = datetime.strptime(partition_key_range.end, partitions_def.fmt)

        parent_start_dt = child_start_dt - partitions_def.delta * start_shift
        parent_end_dt = child_end_dt - partitions_def.delta * end_shift

        return PartitionKeyRange(
            parent_start_dt.strftime(partitions_def.fmt),
            parent_end_dt.strftime(partitions_def.fmt),
        )


def round_datetime_to_period(dt: datetime, period: ScheduleType) -> datetime:
    if period == ScheduleType.MONTHLY:
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == ScheduleType.WEEKLY:
        return (dt - timedelta(days=dt.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    elif period == ScheduleType.DAILY:
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == ScheduleType.HOURLY:
        return dt.replace(minute=0, second=0, microsecond=0)
    else:
        check.failed("Unknown schedule type")
