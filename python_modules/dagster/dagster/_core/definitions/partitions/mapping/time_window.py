from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, NamedTuple, Optional, cast

import dagster._check as check
from dagster._annotations import PublicAttr, beta_param
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.definitions.partitions.definition import (
    PartitionsDefinition,
    TimeWindowPartitionsDefinition,
)
from dagster._core.definitions.partitions.mapping.partition_mapping import (
    PartitionMapping,
    UpstreamPartitionsResult,
)
from dagster._core.definitions.partitions.subset.all import AllPartitionsSubset
from dagster._core.definitions.partitions.subset.partitions_subset import PartitionsSubset
from dagster._core.definitions.partitions.subset.time_window import TimeWindowPartitionsSubset
from dagster._core.definitions.partitions.utils.time_window import TimeWindow
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._serdes import whitelist_for_serdes
from dagster._time import add_absolute_time

if TYPE_CHECKING:
    from dagster._core.instance import DynamicPartitionsStore


@whitelist_for_serdes
@beta_param(param="allow_nonexistent_upstream_partitions")
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

    Args:
        start_offset (int): If not 0, then the starts of the upstream windows are shifted by this
            offset relative to the starts of the downstream windows. For example, if start_offset=-1
            and end_offset=0, then the downstream partition "2022-07-04" would map to the upstream
            partitions "2022-07-03" and "2022-07-04". If the upstream and downstream
            PartitionsDefinitions are different, then the offset is in the units of the downstream.
            Defaults to 0.
        end_offset (int): If not 0, then the ends of the upstream windows are shifted by this
            offset relative to the ends of the downstream windows. For example, if start_offset=0
            and end_offset=1, then the downstream partition "2022-07-04" would map to the upstream
            partitions "2022-07-04" and "2022-07-05". If the upstream and downstream
            PartitionsDefinitions are different, then the offset is in the units of the downstream.
            Defaults to 0.
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
        return super().__new__(
            cls,
            start_offset=check.int_param(start_offset, "start_offset"),
            end_offset=check.int_param(end_offset, "end_offset"),
            allow_nonexistent_upstream_partitions=check.bool_param(
                allow_nonexistent_upstream_partitions,
                "allow_nonexistent_upstream_partitions",
            ),
        )

    @property
    def description(self) -> str:
        description_str = (
            "Maps a downstream partition to any upstream partition with an overlapping time window."
        )

        if self.start_offset != 0 or self.end_offset != 0:
            description_str += (
                f" The start and end of the upstream time window is offsetted by "
                f"{self.start_offset} and {self.end_offset} partitions respectively."
            )

        return description_str

    def _validated_input_partitions_subset(
        self, param_name: str, subset: Optional[PartitionsSubset]
    ) -> TimeWindowPartitionsSubset:
        if isinstance(subset, AllPartitionsSubset):
            return TimeWindowPartitionsSubset.from_all_partitions_subset(subset)
        else:
            return check.inst_param(
                cast("TimeWindowPartitionsSubset", subset),
                param_name,
                TimeWindowPartitionsSubset,
            )

    def _validated_input_partitions_def(
        self, param_name: str, partitions_def: Optional[PartitionsDefinition]
    ) -> TimeWindowPartitionsDefinition:
        return check.inst_param(
            cast("TimeWindowPartitionsDefinition", partitions_def),
            param_name,
            TimeWindowPartitionsDefinition,
        )

    def get_upstream_mapped_partitions_result_for_partitions(
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional["DynamicPartitionsStore"] = None,
    ) -> UpstreamPartitionsResult:
        with partition_loading_context(current_time, dynamic_partitions_store):
            return self._map_partitions(
                from_partitions_def=self._validated_input_partitions_def(
                    "downstream_partitions_def", downstream_partitions_def
                ),
                to_partitions_def=self._validated_input_partitions_def(
                    "upstream_partitions_def", upstream_partitions_def
                ),
                from_partitions_subset=self._validated_input_partitions_subset(
                    "downstream_partitions_subset", downstream_partitions_subset
                ),
                start_offset=self.start_offset,
                end_offset=self.end_offset,
                mapping_downstream_to_upstream=True,
            )

    def validate_partition_mapping(
        self,
        upstream_partitions_def: PartitionsDefinition,
        downstream_partitions_def: Optional[PartitionsDefinition],
    ):
        if not isinstance(downstream_partitions_def, TimeWindowPartitionsDefinition):
            raise DagsterInvalidDefinitionError(
                "Downstream partitions definition must be a TimeWindowPartitionsDefinition",
            )

        if not isinstance(upstream_partitions_def, TimeWindowPartitionsDefinition):
            raise DagsterInvalidDefinitionError(
                "Upstream partitions definition must be a TimeWindowPartitionsDefinition",
            )

        upstream_partitions_def = cast("TimeWindowPartitionsDefinition", upstream_partitions_def)
        downstream_partitions_def = cast(
            "TimeWindowPartitionsDefinition", downstream_partitions_def
        )

        if upstream_partitions_def.timezone != downstream_partitions_def.timezone:
            raise DagsterInvalidDefinitionError(
                f"Timezones {upstream_partitions_def.timezone} and {downstream_partitions_def.timezone} don't match"
            )

    def get_downstream_partitions_for_partitions(
        self,
        upstream_partitions_subset: PartitionsSubset,
        upstream_partitions_def: PartitionsDefinition,
        downstream_partitions_def: Optional[PartitionsDefinition],
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional["DynamicPartitionsStore"] = None,
    ) -> PartitionsSubset:
        """Returns the partitions in the downstream asset that map to the given upstream partitions.

        Filters for partitions that exist at the given current_time, fetching the current time
        if not provided.
        """
        with partition_loading_context(current_time, dynamic_partitions_store):
            return self._map_partitions(
                from_partitions_def=self._validated_input_partitions_def(
                    "upstream_partitions_def", upstream_partitions_def
                ),
                to_partitions_def=self._validated_input_partitions_def(
                    "downstream_partitions_def", downstream_partitions_def
                ),
                from_partitions_subset=self._validated_input_partitions_subset(
                    "upstream_partitions_subset", upstream_partitions_subset
                ),
                end_offset=-self.start_offset,
                start_offset=-self.end_offset,
                mapping_downstream_to_upstream=False,
            ).partitions_subset

    def _merge_time_windows(self, time_windows: Sequence[TimeWindow]) -> Sequence[TimeWindow]:
        """Takes a list of potentially-overlapping TimeWindows and merges any overlapping windows."""
        if not time_windows:
            return []

        sorted_time_windows = sorted(time_windows, key=lambda tw: tw.start.timestamp())
        merged_time_windows: list[TimeWindow] = [sorted_time_windows[0]]

        for window in sorted_time_windows[1:]:
            last_window = merged_time_windows[-1]
            # window starts before the end of the previous one
            if window.start.timestamp() <= last_window.end.timestamp():
                merged_time_windows[-1] = TimeWindow(
                    last_window.start, max(last_window.end, window.end, key=lambda d: d.timestamp())
                )
            else:
                merged_time_windows.append(window)

        return merged_time_windows

    def _map_partitions(
        self,
        from_partitions_def: TimeWindowPartitionsDefinition,
        to_partitions_def: TimeWindowPartitionsDefinition,
        from_partitions_subset: TimeWindowPartitionsSubset,
        start_offset: int,
        end_offset: int,
        mapping_downstream_to_upstream: bool,
    ) -> UpstreamPartitionsResult:
        """Maps the partitions in from_partitions_subset to partitions in to_partitions_def.

        If partitions in from_partitions_subset represent time windows that do not exist in
        to_partitions_def, raises an error if raise_error_on_invalid_mapped_partition is True.
        Otherwise, filters out the partitions that do not exist in to_partitions_def and returns
        the filtered subset, also returning a bool indicating whether there were mapped time windows
        that did not exist in to_partitions_def.

        Args:
            mapping_downstream_to_upstream (bool): True if from_partitions_def is the downstream
                partitions def and to_partitions_def is the upstream partitions def.
        """
        if not isinstance(from_partitions_subset, TimeWindowPartitionsSubset):
            check.failed("from_partitions_subset must be a TimeWindowPartitionsSubset")

        if not isinstance(from_partitions_def, TimeWindowPartitionsDefinition):
            check.failed("from_partitions_def must be a TimeWindowPartitionsDefinition")

        if not isinstance(to_partitions_def, TimeWindowPartitionsDefinition):
            check.failed("to_partitions_def must be a TimeWindowPartitionsDefinition")

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
        )
        if result is not None:
            return result

        first_window = to_partitions_def.get_first_partition_window()
        last_window = to_partitions_def.get_last_partition_window()
        full_window = (
            TimeWindow(first_window.start, last_window.end)
            if first_window is not None and last_window is not None
            else None
        )

        time_windows = []
        for from_partition_time_window in from_partitions_subset.included_time_windows:
            from_start_dt, from_end_dt = (
                from_partition_time_window.start,
                from_partition_time_window.end,
            )

            if mapping_downstream_to_upstream:
                offsetted_from_start_dt = _offsetted_datetime_with_bounds(
                    from_partitions_def, from_start_dt, start_offset, full_window
                )
                offsetted_from_end_dt = _offsetted_datetime_with_bounds(
                    from_partitions_def, from_end_dt, end_offset, full_window
                )
            else:
                # we'll apply the offsets later, after we've found the corresponding windows
                offsetted_from_start_dt = from_start_dt
                offsetted_from_end_dt = from_end_dt

            # Align the windows to partition boundaries in the target PartitionsDefinition
            if (from_partitions_def.cron_schedule == to_partitions_def.cron_schedule) or (
                from_partitions_def.is_basic_daily and to_partitions_def.is_basic_hourly
            ):
                # If the above conditions hold true, then we're confident that the partition
                # boundaries in the PartitionsDefinition that we're mapping from match up with
                # boundaries in the PartitionsDefinition that we're mapping to. That means
                # we can just use these boundaries directly instead of finding nearby boundaries.
                to_start_dt = offsetted_from_start_dt
                to_end_dt = offsetted_from_end_dt
            else:
                # The partition boundaries that we're mapping from might land in the middle of
                # partitions that we're mapping to, so find those partitions.
                to_start_partition_key = to_partitions_def.get_partition_key_for_timestamp(
                    offsetted_from_start_dt.timestamp(), end_closed=False
                )
                to_end_partition_key = to_partitions_def.get_partition_key_for_timestamp(
                    offsetted_from_end_dt.timestamp(), end_closed=True
                )

                to_start_dt = to_partitions_def.start_time_for_partition_key(to_start_partition_key)
                to_end_dt = to_partitions_def.end_time_for_partition_key(to_end_partition_key)

            if mapping_downstream_to_upstream:
                offsetted_to_start_dt = to_start_dt
                offsetted_to_end_dt = to_end_dt
            else:
                offsetted_to_start_dt = _offsetted_datetime_with_bounds(
                    to_partitions_def, to_start_dt, start_offset, full_window
                )
                offsetted_to_end_dt = _offsetted_datetime_with_bounds(
                    to_partitions_def, to_end_dt, end_offset, full_window
                )

            if offsetted_to_start_dt.timestamp() < offsetted_to_end_dt.timestamp():
                time_windows.append(TimeWindow(offsetted_to_start_dt, offsetted_to_end_dt))

        filtered_time_windows = []
        required_but_nonexistent_subset = to_partitions_def.empty_subset()

        for time_window in time_windows:
            if (
                first_window
                and last_window
                and time_window.start.timestamp() <= last_window.start.timestamp()
                and time_window.end.timestamp() >= first_window.end.timestamp()
            ):
                window_start = max(
                    time_window.start, first_window.start, key=lambda d: d.timestamp()
                )
                window_end = min(time_window.end, last_window.end, key=lambda d: d.timestamp())
                filtered_time_windows.append(TimeWindow(window_start, window_end))

            if self.allow_nonexistent_upstream_partitions:
                # If allowed to have nonexistent upstream partitions, do not consider
                # out of range partitions to be invalid
                continue
            else:
                invalid_time_window = None
                if not (first_window and last_window) or (
                    time_window.start.timestamp() < first_window.start.timestamp()
                    and time_window.end.timestamp() > last_window.end.timestamp()
                ):
                    invalid_time_window = time_window
                elif time_window.start.timestamp() < first_window.start.timestamp():
                    invalid_time_window = TimeWindow(
                        time_window.start,
                        min(time_window.end, first_window.start, key=lambda d: d.timestamp()),
                    )
                elif time_window.end.timestamp() > last_window.end.timestamp():
                    invalid_time_window = TimeWindow(
                        max(time_window.start, last_window.end, key=lambda d: d.timestamp()),
                        time_window.end,
                    )

                if invalid_time_window:
                    required_but_nonexistent_subset = (
                        required_but_nonexistent_subset
                        | to_partitions_def.get_partition_subset_in_time_window(
                            time_window=invalid_time_window
                        )
                    )

        return UpstreamPartitionsResult(
            partitions_subset=TimeWindowPartitionsSubset(
                to_partitions_def,
                num_partitions=None,
                included_time_windows=self._merge_time_windows(filtered_time_windows),
            ),
            required_but_nonexistent_subset=required_but_nonexistent_subset,
        )

    def _do_cheap_partition_mapping_if_possible(
        self,
        from_partitions_def: TimeWindowPartitionsDefinition,
        to_partitions_def: TimeWindowPartitionsDefinition,
        from_partitions_subset: TimeWindowPartitionsSubset,
        start_offset: int,
        end_offset: int,
    ) -> Optional[UpstreamPartitionsResult]:
        """The main partition-mapping logic relies heavily on expensive cron iteration operations.

        This method covers a set of easy cases where these operations aren't required. It returns
        None if the mapping doesn't fit into any of these cases.
        """
        if from_partitions_subset.is_empty:
            return UpstreamPartitionsResult(
                partitions_subset=to_partitions_def.empty_subset(),
                required_but_nonexistent_subset=to_partitions_def.empty_subset(),
            )

        if start_offset != 0 or end_offset != 0:
            return None

        # Same PartitionsDefinitions
        if from_partitions_def == to_partitions_def:
            return UpstreamPartitionsResult(
                partitions_subset=from_partitions_subset,
                required_but_nonexistent_subset=to_partitions_def.empty_subset(),
            )

        # Same PartitionsDefinitions except for start and end dates
        if (
            from_partitions_def.equal_except_for_start_or_end(to_partitions_def)
            and (
                from_partitions_def.start.timestamp() >= to_partitions_def.start.timestamp()
                or from_partitions_subset.first_start.timestamp()
                >= to_partitions_def.start.timestamp()
            )
            and (
                to_partitions_def.end is None
                or (
                    from_partitions_def.end is not None
                    and to_partitions_def.end.timestamp() >= from_partitions_def.end.timestamp()
                )
            )
        ):
            return UpstreamPartitionsResult(
                partitions_subset=from_partitions_subset.with_partitions_def(to_partitions_def),
                required_but_nonexistent_subset=to_partitions_def.empty_subset(),
            )

        # Daily to hourly
        from_last_partition_window = from_partitions_def.get_last_partition_window()
        to_last_partition_window = to_partitions_def.get_last_partition_window()
        if (
            from_partitions_def.is_basic_daily
            and to_partitions_def.is_basic_hourly
            and (
                from_partitions_def.start.timestamp() >= to_partitions_def.start.timestamp()
                or from_partitions_subset.first_start.timestamp()
                >= to_partitions_def.start.timestamp()
            )
            and (
                from_last_partition_window is not None
                and to_last_partition_window is not None
                and from_last_partition_window.end.timestamp()
                <= to_last_partition_window.end.timestamp()
            )
        ):
            return UpstreamPartitionsResult(
                partitions_subset=TimeWindowPartitionsSubset(
                    partitions_def=to_partitions_def,
                    num_partitions=None,
                    included_time_windows=from_partitions_subset.included_time_windows,
                ),
                required_but_nonexistent_subset=to_partitions_def.empty_subset(),
            )

        # The subset we're mapping from doesn't exist in the PartitionsDefinition we're mapping to
        if from_partitions_subset.cheap_ends_before(
            to_partitions_def.start, to_partitions_def.cron_schedule
        ):
            if self.allow_nonexistent_upstream_partitions:
                required_but_nonexistent_subset = to_partitions_def.empty_subset()
            else:
                required_but_nonexistent_subset = to_partitions_def.empty_subset()
                for time_window in from_partitions_subset.included_time_windows:
                    required_but_nonexistent_subset = (
                        required_but_nonexistent_subset
                        | to_partitions_def.get_partition_subset_in_time_window(
                            time_window.to_public_time_window()
                        )
                    )

            return UpstreamPartitionsResult(
                partitions_subset=to_partitions_def.empty_subset(),
                required_but_nonexistent_subset=required_but_nonexistent_subset,
            )

        return None


def _offsetted_datetime_with_bounds(
    partitions_def: TimeWindowPartitionsDefinition,
    dt: datetime,
    offset: int,
    bounds_window: Optional[TimeWindow],
) -> datetime:
    offsetted_dt = _offsetted_datetime(partitions_def, dt, offset)

    # Don't allow offsetting to push the windows out of the bounds of the target
    # PartitionsDefinition
    if bounds_window is not None:
        if offset < 0:
            offsetted_dt = max(bounds_window.start, offsetted_dt, key=lambda d: d.timestamp())

        if offset > 0:
            offsetted_dt = min(bounds_window.end, offsetted_dt, key=lambda d: d.timestamp())

    return offsetted_dt


def _offsetted_datetime(
    partitions_def: TimeWindowPartitionsDefinition, dt: datetime, offset: int
) -> datetime:
    if partitions_def.is_basic_daily and offset != 0:
        result = dt + timedelta(days=offset)
        # Handle DST transitions
        if result.hour == 23:
            result = result + timedelta(hours=1)
        elif result.hour == 1:
            result = result - timedelta(hours=1)
        elif result.hour != 0:
            raise Exception(f"Unexpected time after adding day offset {result}")
        return result

    elif partitions_def.is_basic_hourly and offset != 0:
        return add_absolute_time(dt, hours=offset)

    result = dt
    for _ in range(abs(offset)):
        if offset < 0:
            prev_window = cast(
                "TimeWindow",
                partitions_def.get_prev_partition_window(result, respect_bounds=False),
            )
            result = prev_window.start
        else:
            next_window = cast(
                "TimeWindow",
                partitions_def.get_next_partition_window(result, respect_bounds=False),
            )
            result = next_window.end

    return result
