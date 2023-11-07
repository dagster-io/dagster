from datetime import datetime, timedelta
from typing import NamedTuple, Optional, cast

import dagster._check as check
from dagster._annotations import PublicAttr, experimental_param
from dagster._core.definitions.partition import PartitionsDefinition, PartitionsSubset
from dagster._core.definitions.partition_mapping import PartitionMapping, UpstreamPartitionsResult
from dagster._core.definitions.time_window_partitions import (
    BaseTimeWindowPartitionsSubset,
    TimeWindow,
    TimeWindowPartitionsDefinition,
    TimeWindowPartitionsSubset,
)
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.instance import DynamicPartitionsStore
from dagster._serdes import whitelist_for_serdes


@whitelist_for_serdes
@experimental_param(param="allow_nonexistent_upstream_partitions")
class TimeWindowPartitionMapping(
    PartitionMapping,
    NamedTuple(
        "_TimeWindowPartitionMapping",
        [
            ("start_offset", PublicAttr[int]),
            ("end_offset", PublicAttr[int]),
            ("allow_nonexistent_upstream_partitions", PublicAttr[bool]),
        ],
    ),
):
    """The default mapping between two TimeWindowPartitionsDefinitions.

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
        allow_nonexistent_upstream_partitions (bool): Defaults to false. If true, does not
            raise an error when mapped upstream partitions fall outside the start-end time window of the
            partitions def. For example, if the upstream partitions def starts on "2023-01-01" but
            the downstream starts on "2022-01-01", setting this bool to true would return no
            partition keys when get_upstream_partitions_for_partitions is called with "2022-06-01".
            When set to false, would raise an error.

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

    def __new__(
        cls,
        start_offset: int = 0,
        end_offset: int = 0,
        allow_nonexistent_upstream_partitions: bool = False,
    ):
        return super(TimeWindowPartitionMapping, cls).__new__(
            cls,
            start_offset=check.int_param(start_offset, "start_offset"),
            end_offset=check.int_param(end_offset, "end_offset"),
            allow_nonexistent_upstream_partitions=check.bool_param(
                allow_nonexistent_upstream_partitions,
                "allow_nonexistent_upstream_partitions",
            ),
        )

    def get_upstream_mapped_partitions_result_for_partitions(
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        upstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> UpstreamPartitionsResult:
        if not isinstance(downstream_partitions_subset, BaseTimeWindowPartitionsSubset):
            check.failed("downstream_partitions_subset must be a BaseTimeWindowPartitionsSubset")

        return self._map_partitions(
            downstream_partitions_subset.partitions_def,
            upstream_partitions_def,
            downstream_partitions_subset,
            start_offset=self.start_offset,
            end_offset=self.end_offset,
            current_time=current_time,
        )

    def get_downstream_partitions_for_partitions(
        self,
        upstream_partitions_subset: PartitionsSubset,
        downstream_partitions_def: Optional[PartitionsDefinition],
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> PartitionsSubset:
        """Returns the partitions in the downstream asset that map to the given upstream partitions.

        Filters for partitions that exist at the given current_time, fetching the current time
        if not provided.
        """
        return self._map_partitions(
            upstream_partitions_subset.partitions_def,
            downstream_partitions_def,
            upstream_partitions_subset,
            end_offset=-self.start_offset,
            start_offset=-self.end_offset,
            current_time=current_time,
        ).partitions_subset

    def _map_partitions(
        self,
        from_partitions_def: PartitionsDefinition,
        to_partitions_def: Optional[PartitionsDefinition],
        from_partitions_subset: PartitionsSubset,
        start_offset: int,
        end_offset: int,
        current_time: Optional[datetime],
    ) -> UpstreamPartitionsResult:
        """Maps the partitions in from_partitions_subset to partitions in to_partitions_def.

        If partitions in from_partitions_subset represent time windows that do not exist in
        to_partitions_def, raises an error if raise_error_on_invalid_mapped_partition is True.
        Otherwise, filters out the partitions that do not exist in to_partitions_def and returns
        the filtered subset, also returning a bool indicating whether there were mapped time windows
        that did not exist in to_partitions_def.
        """
        if not isinstance(from_partitions_subset, BaseTimeWindowPartitionsSubset):
            check.failed("from_partitions_subset must be a BaseTimeWindowPartitionsSubset")

        if not isinstance(from_partitions_def, TimeWindowPartitionsDefinition):
            check.failed("from_partitions_def must be a TimeWindowPartitionsDefinition")

        if not isinstance(to_partitions_def, TimeWindowPartitionsDefinition):
            check.failed("to_partitions_def must be a TimeWindowPartitionsDefinition")

        if (start_offset != 0 or end_offset != 0) and (
            from_partitions_def.cron_schedule != to_partitions_def.cron_schedule
        ):
            raise DagsterInvalidDefinitionError(
                "Can't use the start_offset or end_offset parameters of"
                " TimeWindowPartitionMapping when the cron schedule of the upstream"
                " PartitionsDefinition is different than the cron schedule of the downstream"
                f" one. Attempted to map from cron schedule '{from_partitions_def.cron_schedule}' "
                f"to cron schedule '{to_partitions_def.cron_schedule}'."
            )

        if to_partitions_def.timezone != from_partitions_def.timezone:
            raise DagsterInvalidDefinitionError(
                f"Timezones {to_partitions_def.timezone} and {from_partitions_def.timezone} don't match"
            )

        result = self._do_cheap_partition_mapping_if_possible(
            from_partitions_def=from_partitions_def,
            to_partitions_def=to_partitions_def,
            from_partitions_subset=from_partitions_subset,
            start_offset=start_offset,
            end_offset=end_offset,
            current_time=current_time,
        )
        if result is not None:
            return result

        first_window = to_partitions_def.get_first_partition_window(current_time=current_time)
        last_window = to_partitions_def.get_last_partition_window(current_time=current_time)

        time_windows = []
        for from_partition_time_window in from_partitions_subset.included_time_windows:
            from_start_dt, from_end_dt = from_partition_time_window

            offsetted_start_dt = _offsetted_datetime(
                from_partitions_def, from_start_dt, start_offset
            )
            offsetted_end_dt = _offsetted_datetime(from_partitions_def, from_end_dt, end_offset)

            # Don't allow offsetting to push the windows out of the bounds of the target
            # PartitionsDefinition
            if first_window is not None and last_window is not None:
                if start_offset < 0:
                    offsetted_start_dt = max(first_window.start, offsetted_start_dt)

                if end_offset < 0:
                    offsetted_end_dt = max(first_window.start, offsetted_end_dt)

                if start_offset > 0:
                    offsetted_start_dt = min(last_window.end, offsetted_start_dt)

                if end_offset > 0:
                    offsetted_end_dt = min(last_window.end, offsetted_end_dt)

            # Align the windows to partition boundaries in the target PartitionsDefinition
            if (from_partitions_def.cron_schedule == to_partitions_def.cron_schedule) or (
                from_partitions_def.is_basic_daily and to_partitions_def.is_basic_hourly
            ):
                # If the above conditions hold true, then we're confident that the partition
                # boundaries in the PartitionsDefinition that we're mapping from match up with
                # boundaries in the PartitionsDefinition that we're mapping to. That means
                # we can just use these boundaries directly instead of finding nearby boundaries.
                window_start = offsetted_start_dt
                window_end = offsetted_end_dt
            else:
                # The partition boundaries that we're mapping from might land in the middle of
                # partitions that we're mapping to, so find those partitions.
                to_start_partition_key = to_partitions_def.get_partition_key_for_timestamp(
                    offsetted_start_dt.timestamp(), end_closed=False
                )
                to_end_partition_key = to_partitions_def.get_partition_key_for_timestamp(
                    offsetted_end_dt.timestamp(), end_closed=True
                )

                window_start = to_partitions_def.start_time_for_partition_key(
                    to_start_partition_key
                )
                window_end = to_partitions_def.end_time_for_partition_key(to_end_partition_key)

            if window_start < window_end:
                time_windows.append(TimeWindow(window_start, window_end))

        filtered_time_windows = []
        required_but_nonexistent_partition_keys = set()

        for time_window in time_windows:
            if (
                first_window
                and last_window
                and time_window.start <= last_window.start
                and time_window.end >= first_window.end
            ):
                window_start = max(time_window.start, first_window.start)
                window_end = min(time_window.end, last_window.end)
                filtered_time_windows.append(TimeWindow(window_start, window_end))

            if self.allow_nonexistent_upstream_partitions:
                # If allowed to have nonexistent upstream partitions, do not consider
                # out of range partitions to be invalid
                continue
            else:
                invalid_time_window = None
                if not (first_window and last_window) or (
                    time_window.start < first_window.start and time_window.end > last_window.end
                ):
                    invalid_time_window = time_window
                elif time_window.start < first_window.start:
                    invalid_time_window = TimeWindow(
                        time_window.start, min(time_window.end, first_window.start)
                    )
                elif time_window.end > last_window.end:
                    invalid_time_window = TimeWindow(
                        max(time_window.start, last_window.end), time_window.end
                    )

                if invalid_time_window:
                    required_but_nonexistent_partition_keys.update(
                        set(
                            to_partitions_def.get_partition_keys_in_time_window(
                                time_window=invalid_time_window
                            )
                        )
                    )

        return UpstreamPartitionsResult(
            TimeWindowPartitionsSubset(
                to_partitions_def, num_partitions=None, included_time_windows=filtered_time_windows
            ),
            sorted(list(required_but_nonexistent_partition_keys)),
        )

    def _do_cheap_partition_mapping_if_possible(
        self,
        from_partitions_def: TimeWindowPartitionsDefinition,
        to_partitions_def: TimeWindowPartitionsDefinition,
        from_partitions_subset: BaseTimeWindowPartitionsSubset,
        start_offset: int,
        end_offset: int,
        current_time: Optional[datetime],
    ) -> Optional[UpstreamPartitionsResult]:
        """The main partition-mapping logic relies heavily on expensive cron iteration operations.

        This method covers a set of easy cases where these operations aren't required. It returns
        None if the mapping doesn't fit into any of these cases.
        """
        if from_partitions_subset.is_empty:
            return UpstreamPartitionsResult(to_partitions_def.empty_subset(), [])

        if start_offset != 0 or end_offset != 0:
            return None

        # Same PartitionsDefinitions
        if from_partitions_def == to_partitions_def:
            return UpstreamPartitionsResult(from_partitions_subset, [])

        # Same PartitionsDefinitions except for start and end dates
        if (
            from_partitions_def.equal_except_for_start_or_end(to_partitions_def)
            and (
                from_partitions_def.start >= to_partitions_def.start
                or from_partitions_subset.first_start >= to_partitions_def.start
            )
            and (
                to_partitions_def.end is None
                or (
                    from_partitions_def.end is not None
                    and to_partitions_def.end >= from_partitions_def.end
                )
            )
        ):
            return UpstreamPartitionsResult(
                from_partitions_subset.with_partitions_def(to_partitions_def), []
            )

        # Daily to hourly
        from_last_partition_window = from_partitions_def.get_last_partition_window(current_time)
        to_last_partition_window = to_partitions_def.get_last_partition_window(current_time)
        if (
            from_partitions_def.is_basic_daily
            and to_partitions_def.is_basic_hourly
            and (
                from_partitions_def.start >= to_partitions_def.start
                or from_partitions_subset.first_start >= to_partitions_def.start
            )
            and (
                from_last_partition_window is not None
                and to_last_partition_window is not None
                and from_last_partition_window.end <= to_last_partition_window.end
            )
        ):
            return UpstreamPartitionsResult(
                TimeWindowPartitionsSubset(
                    partitions_def=to_partitions_def,
                    num_partitions=None,
                    included_time_windows=from_partitions_subset.included_time_windows,
                ),
                [],
            )

        # The subset we're mapping from doesn't exist in the PartitionsDefinition we're mapping to
        if from_partitions_subset.cheap_ends_before(
            to_partitions_def.start, to_partitions_def.cron_schedule
        ):
            if self.allow_nonexistent_upstream_partitions:
                required_but_nonexistent_partition_keys = []
            else:
                required_but_nonexistent_partition_keys = [
                    pk
                    for time_window in from_partitions_subset.included_time_windows
                    for pk in to_partitions_def.get_partition_keys_in_time_window(
                        time_window=time_window
                    )
                ]

            return UpstreamPartitionsResult(
                to_partitions_def.empty_subset(), required_but_nonexistent_partition_keys
            )

        return None


def _offsetted_datetime(
    partitions_def: TimeWindowPartitionsDefinition, dt: datetime, offset: int
) -> datetime:
    if partitions_def.is_basic_daily and offset != 0:
        result = dt + timedelta(days=offset)

        if result.hour == dt.hour:
            # Can't short-circuit in cases where a DST transition moved us
            # to a different hour, fall back to slow logic
            return result

    elif partitions_def.is_basic_hourly and offset != 0:
        return dt + timedelta(hours=offset)

    result = dt
    for _ in range(abs(offset)):
        if offset < 0:
            prev_window = cast(
                TimeWindow,
                partitions_def.get_prev_partition_window(result, respect_bounds=False),
            )
            result = prev_window.start
        else:
            next_window = cast(
                TimeWindow,
                partitions_def.get_next_partition_window(result, respect_bounds=False),
            )
            result = next_window.end

    return result
