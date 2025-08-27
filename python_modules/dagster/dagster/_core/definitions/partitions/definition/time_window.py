import functools
import hashlib
import re
from collections.abc import Iterable, Sequence
from datetime import date, datetime
from functools import cached_property
from typing import TYPE_CHECKING, Optional, Union, cast

import dagster._check as check
from dagster._annotations import PublicAttr, public
from dagster._core.definitions.partitions.context import (
    PartitionLoadingContext,
    partition_loading_context,
)
from dagster._core.definitions.partitions.definition.partitions_definition import (
    PartitionsDefinition,
)
from dagster._core.definitions.partitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.partitions.schedule_type import (
    ScheduleType,
    cron_schedule_from_schedule_type_and_offsets,
)
from dagster._core.definitions.partitions.utils.time_window import TimeWindow, TimeWindowCursor
from dagster._core.definitions.timestamp import TimestampWithTimezone
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.types.pagination import PaginatedResults
from dagster._record import IHaveNew, record_custom
from dagster._serdes import whitelist_for_serdes
from dagster._time import (
    datetime_from_timestamp,
    dst_safe_strftime,
    dst_safe_strptime,
    get_timezone,
)
from dagster._utils.cronstring import get_fixed_minute_interval, is_basic_daily, is_basic_hourly
from dagster._utils.schedules import (
    cron_string_iterator,
    is_valid_cron_schedule,
    reverse_cron_string_iterator,
)

if TYPE_CHECKING:
    from dagster._core.definitions.partitions.subset.partitions_subset import PartitionsSubset
    from dagster._core.definitions.partitions.subset.time_window import TimeWindowPartitionsSubset
    from dagster._core.instance import DynamicPartitionsStore


@whitelist_for_serdes
@record_custom(
    field_to_new_mapping={
        "start_ts": "start",
        "end_ts": "end",
    }
)
class TimeWindowPartitionsDefinition(PartitionsDefinition, IHaveNew):
    r"""A set of partitions where each partition corresponds to a time window.

    The provided cron_schedule determines the bounds of the time windows. E.g. a cron_schedule of
    "0 0 \\* \\* \\*" will result in daily partitions that start at midnight and end at midnight of the
    following day.

    The string partition_key associated with each partition corresponds to the start of the
    partition's time window.

    The first partition in the set will start on at the first cron_schedule tick that is equal to
    or after the given start datetime. The last partition in the set will end before the current
    time, unless the end_offset argument is set to a positive number.

    We recommended limiting partition counts for each asset to 100,000 partitions or fewer.

    Args:
        cron_schedule (str): Determines the bounds of the time windows.
        start (datetime): The first partition in the set will start on at the first cron_schedule
            tick that is equal to or after this value.
        timezone (Optional[str]): The timezone in which each time should exist.
            Supported strings for timezones are the ones provided by the
            `IANA time zone database <https://www.iana.org/time-zones>`_ - e.g. "America/Los_Angeles".

        end (datetime): The last partition (excluding) in the set.
        fmt (str): The date format to use for partition_keys. Note that if a non-UTC timezone is
            used, and the cron schedule repeats every hour or faster, the date format must include
            a timezone offset to disambiguate between multiple instances of the same time before and
            after the Fall DST transition. If the format does not contain this offset, the second
            instance of the ambiguous time partition key will have the UTC offset automatically
            appended to it.
        end_offset (int): Extends the partition set by a number of partitions equal to the value
            passed. If end_offset is 0 (the default), the last partition ends before the current
            time. If end_offset is 1, the second-to-last partition ends before the current time,
            and so on.
        exclusions (Optional[Sequence[Union[str, datetime]]]): Specifies a sequence of cron strings
            or datetime objects that should be excluded from the partition set. Every tick of the
            cron schedule that matches an excluded datetime or matches the tick of an excluded
            cron string will be excluded from the partition set.

    """

    start_ts: TimestampWithTimezone
    timezone: PublicAttr[str]
    end_ts: Optional[TimestampWithTimezone]
    fmt: PublicAttr[str]
    end_offset: PublicAttr[int]
    cron_schedule: PublicAttr[str]
    exclusions: PublicAttr[Optional[Sequence[Union[str, TimestampWithTimezone]]]]

    def __new__(
        cls,
        start: Union[datetime, str, TimestampWithTimezone],
        fmt: str,
        end: Union[datetime, str, TimestampWithTimezone, None] = None,
        schedule_type: Optional[ScheduleType] = None,
        timezone: Optional[str] = None,
        end_offset: int = 0,
        minute_offset: Optional[int] = None,
        hour_offset: Optional[int] = None,
        day_offset: Optional[int] = None,
        cron_schedule: Optional[str] = None,
        exclusions: Optional[Sequence[Union[str, datetime, TimestampWithTimezone]]] = None,
    ):
        check.opt_str_param(timezone, "timezone")
        timezone = timezone or "UTC"

        if isinstance(start, str):
            start_dt = dst_safe_strptime(start, timezone, fmt)
            start = TimestampWithTimezone(start_dt.timestamp(), timezone)
        elif isinstance(start, datetime):
            start_dt = start.replace(tzinfo=get_timezone(timezone))
            start = TimestampWithTimezone(start_dt.timestamp(), timezone)

        if not end:
            end = None
        elif isinstance(end, str):
            end_dt = dst_safe_strptime(end, timezone, fmt)
            end = TimestampWithTimezone(end_dt.timestamp(), timezone)
        elif isinstance(end, datetime):
            end_dt = end.replace(tzinfo=get_timezone(timezone))
            end = TimestampWithTimezone(end_dt.timestamp(), timezone)

        if cron_schedule is not None:
            check.invariant(
                schedule_type is None and not minute_offset and not hour_offset and not day_offset,
                "If cron_schedule argument is provided, then schedule_type, minute_offset, "
                "hour_offset, and day_offset can't also be provided",
            )
        else:
            if schedule_type is None:
                check.failed("One of schedule_type and cron_schedule must be provided")

            cron_schedule = cron_schedule_from_schedule_type_and_offsets(
                schedule_type=schedule_type,
                minute_offset=minute_offset or 0,
                hour_offset=hour_offset or 0,
                day_offset=day_offset or 0,
            )

        if not is_valid_cron_schedule(cron_schedule):
            raise DagsterInvalidDefinitionError(
                f"Found invalid cron schedule '{cron_schedule}' for a"
                " TimeWindowPartitionsDefinition."
            )

        cleaned_exclusions: Optional[Sequence[Union[str, TimestampWithTimezone]]] = None
        if exclusions:
            check.sequence_param(
                exclusions,
                "exclusions",
                of_type=(str, datetime, TimestampWithTimezone),
            )
            cron_exclusions = [cs for cs in exclusions if isinstance(cs, str)]
            invalid_exclusions = [cs for cs in cron_exclusions if not is_valid_cron_schedule(cs)]
            if invalid_exclusions:
                quoted_exclusions = [f"'{excl}'" for excl in invalid_exclusions]
                invalid_exclusion_str = ", ".join(quoted_exclusions)
                raise DagsterInvalidDefinitionError(
                    f"Found invalid cron schedule(s) {invalid_exclusion_str} in the exclusions"
                    " argument for a TimeWindowPartitionsDefinition. Expected a set of valid cron"
                    " strings and datetime objects."
                )
            cleaned_exclusions = []
            for exclusion_part in exclusions:
                if isinstance(exclusion_part, datetime):
                    dt = exclusion_part.replace(tzinfo=get_timezone(timezone))
                    cleaned_exclusions.append(TimestampWithTimezone(dt.timestamp(), timezone))
                else:
                    cleaned_exclusions.append(exclusion_part)

        return super().__new__(
            cls,
            start_ts=start,
            timezone=timezone,
            end_ts=end,
            fmt=fmt,
            end_offset=end_offset,
            cron_schedule=cron_schedule,
            exclusions=cleaned_exclusions if cleaned_exclusions else None,
        )

    @property
    def start_timestamp(self) -> float:
        return self.start_ts.timestamp

    @property
    def end_timestamp(self) -> Optional[float]:
        return self.end_ts.timestamp if self.end_ts else None

    @public
    @cached_property
    def start(self) -> datetime:
        start_timestamp_with_timezone = self.start_ts
        return datetime_from_timestamp(
            start_timestamp_with_timezone.timestamp, start_timestamp_with_timezone.timezone
        )

    @public
    @cached_property
    def end(self) -> Optional[datetime]:
        end_timestamp_with_timezone = self.end_ts

        if not end_timestamp_with_timezone:
            return None

        return datetime.fromtimestamp(
            end_timestamp_with_timezone.timestamp,
            get_timezone(end_timestamp_with_timezone.timezone),
        )

    def _get_current_timestamp(self) -> float:
        with partition_loading_context() as ctx:
            current_time = ctx.effective_dt
            # if a naive current time was passed in, assume it was the same timezone as the partition set
            if not current_time.tzinfo:
                current_time = current_time.replace(tzinfo=get_timezone(self.timezone))

            return current_time.timestamp()

    def get_num_partitions_in_window(self, time_window: TimeWindow) -> int:
        if time_window.start.timestamp() >= time_window.end.timestamp():
            return 0
        if self.is_basic_daily:
            return (
                date(
                    time_window.end.year,
                    time_window.end.month,
                    time_window.end.day,
                )
                - date(
                    time_window.start.year,
                    time_window.start.month,
                    time_window.start.day,
                )
            ).days

        fixed_minute_interval = get_fixed_minute_interval(self.cron_schedule)
        if fixed_minute_interval and not self.exclusions:
            minutes_in_window = (time_window.end.timestamp() - time_window.start.timestamp()) / 60
            return int(minutes_in_window // fixed_minute_interval)

        return len(self.get_partition_keys_in_time_window(time_window))

    def get_num_partitions(self) -> int:
        last_partition_window = self.get_last_partition_window()
        first_partition_window = self.get_first_partition_window()

        if not last_partition_window or not first_partition_window:
            return 0

        return self.get_num_partitions_in_window(
            TimeWindow(start=first_partition_window.start, end=last_partition_window.end)
        )

    def get_partition_keys_between_indexes(self, start_idx: int, end_idx: int) -> list[str]:
        # Fetches the partition keys between the given start and end indices.
        # Start index is inclusive, end index is exclusive.
        # Method added for performance reasons, to only string format
        # partition keys included within the indices.
        current_timestamp = self._get_current_timestamp()

        partitions_past_current_time = 0
        partition_keys = []
        reached_end = False

        for idx, time_window in enumerate(self._iterate_time_windows(self.start_timestamp)):
            if time_window.end.timestamp() >= current_timestamp:
                reached_end = True
            if self.end_timestamp is not None and time_window.end.timestamp() > self.end_timestamp:
                reached_end = True
            if (
                time_window.end.timestamp() <= current_timestamp
                or partitions_past_current_time < self.end_offset
            ):
                if idx >= start_idx and idx < end_idx:
                    partition_keys.append(
                        dst_safe_strftime(
                            time_window.start, self.timezone, self.fmt, self.cron_schedule
                        )
                    )
                if time_window.end.timestamp() > current_timestamp:
                    partitions_past_current_time += 1
            else:
                break
            if len(partition_keys) >= end_idx - start_idx:
                break

        if reached_end and self.end_offset < 0:
            partition_keys = partition_keys[: self.end_offset]

        return partition_keys

    def is_window_start_excluded(self, window_start: datetime):
        if not self.exclusions:
            return False

        start_ts = TimestampWithTimezone(
            window_start.replace(tzinfo=get_timezone(self.timezone)).timestamp(), self.timezone
        )
        if start_ts in self.exclusions:
            return True

        excluded_cron_strings = [
            cron_string for cron_string in self.exclusions if isinstance(cron_string, str)
        ]
        for cron_string in excluded_cron_strings:
            if window_start == next(
                cron_string_iterator(window_start.timestamp(), cron_string, self.timezone)
            ):
                return True
        return False

    def get_partition_keys(
        self,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional["DynamicPartitionsStore"] = None,
    ) -> Sequence[str]:
        with partition_loading_context(current_time, dynamic_partitions_store):
            current_timestamp = self._get_current_timestamp()

            last_partition_window = self._get_last_partition_window(current_timestamp)
            if not last_partition_window:
                return []

            partition_keys = []

            for time_window in self._iterate_time_windows(self.start_timestamp):
                partition_keys.append(
                    dst_safe_strftime(
                        time_window.start, self.timezone, self.fmt, self.cron_schedule
                    )
                )

                if time_window.start.timestamp() >= last_partition_window.start.timestamp():
                    break

            return partition_keys

    def get_paginated_partition_keys(
        self,
        context: PartitionLoadingContext,
        limit: int,
        ascending: bool,
        cursor: Optional[str] = None,
    ) -> PaginatedResults[str]:
        with partition_loading_context(new_ctx=context):
            current_timestamp = self._get_current_timestamp()

            if cursor:
                time_window_cursor = TimeWindowCursor.from_cursor(cursor)
                start_timestamp = time_window_cursor.start_timestamp
                end_timestamp = time_window_cursor.end_timestamp
                offset_partitions_count = time_window_cursor.offset_partition_count
            else:
                start_timestamp = self.start_timestamp
                end_timestamp = current_timestamp
                offset_partitions_count = 0

            partition_keys: list[str] = []
            has_more = False

            if not ascending:
                offset_time_windows = []
                if self.end_offset > 0 and self.end_offset > offset_partitions_count:
                    last_no_offset_time_window = next(
                        iter(self._reverse_iterate_time_windows(end_timestamp)), None
                    )
                    lookforward_time = (
                        last_no_offset_time_window.end.timestamp()
                        if last_no_offset_time_window
                        else end_timestamp
                    )
                    for time_window in self._iterate_time_windows(lookforward_time):
                        if (
                            self.end_timestamp is not None
                            and time_window.end.timestamp() > self.end_timestamp
                        ):
                            break

                        if len(offset_time_windows) >= self.end_offset - offset_partitions_count:
                            break

                        if not self.is_window_start_excluded(time_window.start):
                            offset_time_windows.append(
                                dst_safe_strftime(
                                    time_window.start, self.timezone, self.fmt, self.cron_schedule
                                )
                            )

                partition_keys = list(reversed(offset_time_windows))[:limit]
                offset_partitions_count += len(partition_keys)

                for time_window in self._reverse_iterate_time_windows(end_timestamp):
                    if len(partition_keys) >= limit - min(0, self.end_offset):
                        has_more = True
                        break

                    if time_window.start.timestamp() < start_timestamp:
                        break

                    partition_keys.append(
                        dst_safe_strftime(
                            time_window.start, self.timezone, self.fmt, self.cron_schedule
                        )
                    )

                if self.end_offset < 0 and not cursor:
                    # only subset if we did not have a cursor... if we did have a cursor, we've already
                    # applied the offset to the end, since we're moving backwards from the end
                    partition_keys = partition_keys[-1 * min(0, self.end_offset) :]

            else:
                for time_window in self._iterate_time_windows(start_timestamp):
                    if (
                        self.end_timestamp is not None
                        and time_window.end.timestamp() > self.end_timestamp
                    ):
                        break
                    if (
                        time_window.end.timestamp() <= end_timestamp
                        or offset_partitions_count < self.end_offset
                    ):
                        partition_keys.append(
                            dst_safe_strftime(
                                time_window.start, self.timezone, self.fmt, self.cron_schedule
                            )
                        )
                        if time_window.end.timestamp() > end_timestamp:
                            offset_partitions_count += 1
                        if len(partition_keys) >= limit - min(0, self.end_offset):
                            has_more = True
                            break
                    else:
                        break

                if has_more:
                    # exited due to limit; subset in case we overshot (if end_offset < 0)
                    partition_keys = partition_keys[:limit]
                elif self.end_offset < 0:
                    # only subset if we did not eject early due to the limit
                    partition_keys = partition_keys[: self.end_offset]

            if not partition_keys:
                next_cursor = TimeWindowCursor(
                    start_timestamp=int(start_timestamp),
                    end_timestamp=int(end_timestamp),
                    offset_partition_count=offset_partitions_count,
                )
            elif ascending:
                last_partition_key = partition_keys[-1]
                last_time_window = self.time_window_for_partition_key(last_partition_key)
                next_cursor = TimeWindowCursor(
                    start_timestamp=int(last_time_window.end.timestamp()),
                    end_timestamp=int(end_timestamp),
                    offset_partition_count=offset_partitions_count,
                )
            else:
                last_partition_key = partition_keys[-1]
                last_time_window = self.time_window_for_partition_key(last_partition_key)
                next_cursor = TimeWindowCursor(
                    start_timestamp=int(start_timestamp),
                    end_timestamp=int(end_timestamp)
                    if self.end_offset > 0 and offset_partitions_count < self.end_offset
                    else int(last_time_window.start.timestamp()),
                    offset_partition_count=offset_partitions_count,
                )

            return PaginatedResults(
                results=partition_keys,
                cursor=str(next_cursor),
                has_more=has_more,
            )

    def __str__(self) -> str:
        schedule_str = (
            self.schedule_type.value.capitalize() if self.schedule_type else self.cron_schedule
        )
        partition_def_str = f"{schedule_str}, starting {dst_safe_strftime(self.start, self.timezone, self.fmt, self.cron_schedule)} {self.timezone}."
        if self.end_offset != 0:
            partition_def_str += (
                " End offsetted by"
                f" {self.end_offset} partition{'' if self.end_offset == 1 else 's'}."
            )
        return partition_def_str

    def __repr__(self):
        # Between python 3.8 and 3.9 the repr of a datetime object changed.
        # Replaces start time with timestamp as a workaround to make sure the repr is consistent across versions.
        # Make sure to update this __repr__ if any new fields are added to TimeWindowPartitionsDefinition.
        exclusions_str = f", exclusions={self.exclusions}" if self.exclusions else ""
        return (
            f"TimeWindowPartitionsDefinition(start={self.start_timestamp},"
            f" end={self.end_timestamp if self.end_timestamp is not None else None},"
            f" timezone='{self.timezone}', fmt='{self.fmt}', end_offset={self.end_offset},"
            f" cron_schedule='{self.cron_schedule}')"
        ) + exclusions_str

    def __hash__(self):
        return hash(tuple(self.__repr__()))

    @functools.lru_cache(maxsize=100)
    def time_window_for_partition_key(self, partition_key: str) -> TimeWindow:
        partition_key_dt = dst_safe_strptime(partition_key, self.timezone, self.fmt)
        return next(iter(self._iterate_time_windows(partition_key_dt.timestamp())))

    @functools.lru_cache(maxsize=5)
    def time_windows_for_partition_keys(
        self, partition_keys: frozenset[str], validate: bool = True
    ) -> Sequence[TimeWindow]:
        if len(partition_keys) == 0:
            return []

        sorted_pks = sorted(
            partition_keys,
            key=lambda pk: dst_safe_strptime(pk, self.timezone, self.fmt).timestamp(),
        )
        cur_windows_iterator = iter(
            self._iterate_time_windows(
                dst_safe_strptime(sorted_pks[0], self.timezone, self.fmt).timestamp()
            )
        )
        partition_key_time_windows: list[TimeWindow] = []
        for partition_key in sorted_pks:
            next_window = next(cur_windows_iterator)
            if (
                dst_safe_strftime(next_window.start, self.timezone, self.fmt, self.cron_schedule)
                == partition_key
            ):
                partition_key_time_windows.append(next_window)
            else:
                cur_windows_iterator = iter(
                    self._iterate_time_windows(
                        dst_safe_strptime(partition_key, self.timezone, self.fmt).timestamp()
                    )
                )
                partition_key_time_windows.append(next(cur_windows_iterator))

        if validate:
            start_time_window = self.get_first_partition_window()
            end_time_window = self.get_last_partition_window()

            if start_time_window is None or end_time_window is None:
                check.failed("No partitions in the PartitionsDefinition")

            start_timestamp = start_time_window.start.timestamp()
            end_timestamp = end_time_window.end.timestamp()

            partition_key_time_windows = [
                tw
                for tw in partition_key_time_windows
                if tw.start.timestamp() >= start_timestamp and tw.end.timestamp() <= end_timestamp
            ]
        return partition_key_time_windows

    def start_time_for_partition_key(self, partition_key: str) -> datetime:
        partition_key_dt = dst_safe_strptime(partition_key, self.timezone, self.fmt)
        if self.is_basic_hourly or self.is_basic_daily:
            return partition_key_dt
        # the datetime format might not include granular components, so we need to recover them,
        # e.g. if cron_schedule="0 7 * * *" and fmt="%Y-%m-%d".
        # we make the assumption that the parsed partition key is <= the start datetime.
        return next(iter(self._iterate_time_windows(partition_key_dt.timestamp()))).start

    def get_next_partition_key(self, partition_key: str) -> Optional[str]:
        last_partition_window = self.get_last_partition_window()
        if last_partition_window is None:
            return None

        partition_key_dt = dst_safe_strptime(partition_key, self.timezone, self.fmt)
        windows_iter = iter(self._iterate_time_windows(partition_key_dt.timestamp()))
        next(windows_iter)
        start_time = next(windows_iter).start
        if start_time.timestamp() >= last_partition_window.end.timestamp():
            return None
        else:
            return dst_safe_strftime(start_time, self.timezone, self.fmt, self.cron_schedule)

    def get_next_partition_window(
        self, end_dt: datetime, respect_bounds: bool = True
    ) -> Optional[TimeWindow]:
        windows_iter = iter(self._iterate_time_windows(end_dt.timestamp()))
        next_window = next(windows_iter)

        if respect_bounds:
            last_partition_window = self.get_last_partition_window()
            if last_partition_window is None:
                return None

            if next_window.start.timestamp() >= last_partition_window.end.timestamp():
                return None

        return next_window

    def get_prev_partition_window(
        self, start_dt: datetime, respect_bounds: bool = True
    ) -> Optional[TimeWindow]:
        windows_iter = iter(self._reverse_iterate_time_windows(start_dt.timestamp()))
        prev_window = next(windows_iter)
        if respect_bounds:
            first_partition_window = self.get_first_partition_window()
            if (
                first_partition_window is None
                or prev_window.start.timestamp() < first_partition_window.start.timestamp()
            ):
                return None

        return prev_window

    @functools.lru_cache(maxsize=256)
    def _get_first_partition_window(self, current_timestamp: float) -> Optional[TimeWindow]:
        time_window = next(iter(self._iterate_time_windows(self.start_timestamp)))

        if self.end_timestamp is not None and self.end_timestamp <= self.start_timestamp:
            return None

        if self.end_offset == 0:
            return time_window if time_window.end.timestamp() <= current_timestamp else None
        elif self.end_offset > 0:
            iterator = iter(self._iterate_time_windows(current_timestamp))
            # first returned time window is time window of current time
            curr_window_plus_offset = next(iterator)
            for _ in range(self.end_offset):
                curr_window_plus_offset = next(iterator)
            return (
                time_window
                if time_window.end.timestamp() <= curr_window_plus_offset.start.timestamp()
                else None
            )
        else:
            # end offset < 0
            end_window = None
            iterator = iter(self._reverse_iterate_time_windows(current_timestamp))
            for _ in range(abs(self.end_offset)):
                end_window = next(iterator)

            if end_window is None:
                check.failed("end_window should not be None")

            return (
                time_window if time_window.end.timestamp() <= end_window.start.timestamp() else None
            )

    def get_first_partition_window(self) -> Optional[TimeWindow]:
        return self._get_first_partition_window(self._get_current_timestamp())

    @functools.lru_cache(maxsize=256)
    def _get_last_partition_window(
        self, current_timestamp: float, ignore_exclusions: bool = False
    ) -> Optional[TimeWindow]:
        first_window = self.get_first_partition_window()
        if first_window is None:
            return None

        if self.end_offset == 0:
            if self.end_timestamp is not None and self.end_timestamp < current_timestamp:
                current_timestamp = self.end_timestamp

            return next(
                iter(
                    self._reverse_iterate_time_windows(
                        current_timestamp, ignore_exclusions=ignore_exclusions
                    )
                )
            )

        last_window_before_end_timestamp = None
        current_timestamp_window = None

        if self.end_timestamp is not None:
            last_window_before_end_timestamp = next(
                iter(
                    self._reverse_iterate_time_windows(
                        self.end_timestamp, ignore_exclusions=ignore_exclusions
                    )
                )
            )

        current_timestamp_iter = iter(
            self._reverse_iterate_time_windows(
                current_timestamp, ignore_exclusions=ignore_exclusions
            )
        )
        # first returned time window is the last window <= the current timestamp
        end_offset_zero_window = next(current_timestamp_iter)

        if self.end_offset < 0:
            for _ in range(abs(self.end_offset)):
                current_timestamp_window = next(current_timestamp_iter)
        else:
            current_timestamp_iter = iter(
                self._iterate_time_windows(
                    end_offset_zero_window.end.timestamp(), ignore_exclusions=ignore_exclusions
                )
            )
            for _ in range(self.end_offset):
                current_timestamp_window = next(current_timestamp_iter)

        current_timestamp_window = check.not_none(
            current_timestamp_window,
            "current_timestamp_window should not be None if end_offset != 0",
        )

        if (
            last_window_before_end_timestamp
            and last_window_before_end_timestamp.start.timestamp()
            <= current_timestamp_window.start.timestamp()
        ):
            return last_window_before_end_timestamp
        elif current_timestamp_window.start.timestamp() < first_window.start.timestamp():
            return first_window
        else:
            return current_timestamp_window

    def get_last_partition_window(self) -> Optional[TimeWindow]:
        return self._get_last_partition_window(
            self._get_current_timestamp(), ignore_exclusions=False
        )

    def get_last_partition_window_ignoring_exclusions(self) -> Optional[TimeWindow]:
        return self._get_last_partition_window(
            self._get_current_timestamp(), ignore_exclusions=True
        )

    def get_first_partition_key(self) -> Optional[str]:
        first_window = self.get_first_partition_window()
        if first_window is None:
            return None

        return dst_safe_strftime(first_window.start, self.timezone, self.fmt, self.cron_schedule)

    def get_last_partition_key(self) -> Optional[str]:
        last_window = self.get_last_partition_window()
        if last_window is None:
            return None

        return dst_safe_strftime(last_window.start, self.timezone, self.fmt, self.cron_schedule)

    def end_time_for_partition_key(self, partition_key: str) -> datetime:
        return self.time_window_for_partition_key(partition_key).end

    @functools.lru_cache(maxsize=5)
    def get_partition_keys_in_time_window(self, time_window: TimeWindow) -> Sequence[str]:
        result: list[str] = []
        time_window_end_timestamp = time_window.end.timestamp()
        for partition_time_window in self._iterate_time_windows(time_window.start.timestamp()):
            if partition_time_window.start.timestamp() < time_window_end_timestamp:
                result.append(
                    dst_safe_strftime(
                        partition_time_window.start, self.timezone, self.fmt, self.cron_schedule
                    )
                )
            else:
                break
        return result

    def get_partition_subset_in_time_window(
        self, time_window: TimeWindow
    ) -> "TimeWindowPartitionsSubset":
        return self.partitions_subset_class(
            partitions_def=self, num_partitions=None, included_time_windows=[time_window]
        )

    def get_partition_key_range_for_time_window(
        self, time_window: TimeWindow, respect_bounds: bool = True
    ) -> PartitionKeyRange:
        start_partition_key = self.get_partition_key_for_timestamp(time_window.start.timestamp())
        end_partition_key = self.get_partition_key_for_timestamp(
            check.not_none(
                self.get_prev_partition_window(time_window.end, respect_bounds=respect_bounds)
            ).start.timestamp()
        )

        return PartitionKeyRange(start_partition_key, end_partition_key)

    def get_partition_keys_in_range(self, partition_key_range: PartitionKeyRange) -> Sequence[str]:
        start_time = self.start_time_for_partition_key(partition_key_range.start)
        check.invariant(
            start_time.timestamp() >= self.start_timestamp,
            (
                f"Partition key range start {partition_key_range.start} is before "
                f"the partitions definition start time {self.start}"
            ),
        )
        end_time = self.end_time_for_partition_key(partition_key_range.end)
        if self.end_timestamp is not None:
            check.invariant(
                end_time.timestamp() <= self.end_timestamp,
                (
                    f"Partition key range end {partition_key_range.end} is after the "
                    f"partitions definition end time {self.end}"
                ),
            )

        return self.get_partition_keys_in_time_window(TimeWindow(start_time, end_time))

    @public
    @property
    def schedule_type(self) -> Optional[ScheduleType]:
        """Optional[ScheduleType]: An enum representing the partition cadence (hourly, daily,
        weekly, or monthly).
        """
        if re.fullmatch(r"\d+ \* \* \* \*", self.cron_schedule):
            return ScheduleType.HOURLY
        elif re.fullmatch(r"\d+ \d+ \* \* \*", self.cron_schedule):
            return ScheduleType.DAILY
        elif re.fullmatch(r"\d+ \d+ \* \* \d+", self.cron_schedule):
            return ScheduleType.WEEKLY
        elif re.fullmatch(r"\d+ \d+ \d+ \* \*", self.cron_schedule):
            return ScheduleType.MONTHLY
        else:
            return None

    @public
    @property
    def minute_offset(self) -> int:
        """int: Number of minutes past the hour to "split" partitions. Defaults to 0.

        For example, returns 15 if each partition starts at 15 minutes past the hour.
        """
        match = re.fullmatch(r"(\d+) (\d+|\*) (\d+|\*) (\d+|\*) (\d+|\*)", self.cron_schedule)
        if match is None:
            check.failed(f"{self.cron_schedule} has no minute offset")
        return int(match.groups()[0])

    @public
    @property
    def hour_offset(self) -> int:
        """int: Number of hours past 00:00 to "split" partitions. Defaults to 0.

        For example, returns 1 if each partition starts at 01:00.
        """
        match = re.fullmatch(r"(\d+|\*) (\d+) (\d+|\*) (\d+|\*) (\d+|\*)", self.cron_schedule)
        if match is None:
            check.failed(f"{self.cron_schedule} has no hour offset")
        return int(match.groups()[1])

    @public
    @property
    def day_offset(self) -> int:
        """int: For a weekly or monthly partitions definition, returns the day to "split" partitions
        by. Each partition will start on this day, and end before this day in the following
        week/month. Returns 0 if the day_offset parameter is unset in the
        WeeklyPartitionsDefinition, MonthlyPartitionsDefinition, or the provided cron schedule.

        For weekly partitions, returns a value between 0 (representing Sunday) and 6 (representing
        Saturday). Providing a value of 1 means that a partition will exist weekly from Monday to
        the following Sunday.

        For monthly partitions, returns a value between 0 (the first day of the month) and 31 (the
        last possible day of the month).
        """
        schedule_type = self.schedule_type
        if schedule_type == ScheduleType.WEEKLY:
            match = re.fullmatch(r"(\d+|\*) (\d+|\*) (\d+|\*) (\d+|\*) (\d+)", self.cron_schedule)
            if match is None:
                check.failed(f"{self.cron_schedule} has no day offset")
            return int(match.groups()[4])
        elif schedule_type == ScheduleType.MONTHLY:
            match = re.fullmatch(r"(\d+|\*) (\d+|\*) (\d+) (\d+|\*) (\d+|\*)", self.cron_schedule)
            if match is None:
                check.failed(f"{self.cron_schedule} has no day offset")
            return int(match.groups()[2])
        else:
            check.failed(f"Unsupported schedule type for day_offset: {schedule_type}")

    @public
    def get_cron_schedule(
        self,
        minute_of_hour: Optional[int] = None,
        hour_of_day: Optional[int] = None,
        day_of_week: Optional[int] = None,
        day_of_month: Optional[int] = None,
    ) -> str:
        """The schedule executes at the cadence specified by the partitioning, but may overwrite
        the minute/hour/day offset of the partitioning.

        This is useful e.g. if you have partitions that span midnight to midnight but you want to
        schedule a job that runs at 2 am.
        """
        if (
            minute_of_hour is None
            and hour_of_day is None
            and day_of_week is None
            and day_of_month is None
        ):
            return self.cron_schedule

        schedule_type = self.schedule_type
        if schedule_type is None:
            check.failed(
                f"{self.cron_schedule} does not support"
                " minute_of_hour/hour_of_day/day_of_week/day_of_month arguments"
            )

        minute_of_hour = cast(
            "int",
            check.opt_int_param(minute_of_hour, "minute_of_hour", default=self.minute_offset),
        )

        if schedule_type == ScheduleType.HOURLY:
            check.invariant(
                hour_of_day is None, "Cannot set hour parameter with hourly partitions."
            )
        else:
            hour_of_day = cast(
                "int", check.opt_int_param(hour_of_day, "hour_of_day", default=self.hour_offset)
            )

        if schedule_type == ScheduleType.DAILY:
            check.invariant(
                day_of_week is None, "Cannot set day of week parameter with daily partitions."
            )
            check.invariant(
                day_of_month is None, "Cannot set day of month parameter with daily partitions."
            )

        if schedule_type == ScheduleType.MONTHLY:
            default = self.day_offset or 1
            day_offset = check.opt_int_param(day_of_month, "day_of_month", default=default)
        elif schedule_type == ScheduleType.WEEKLY:
            default = self.day_offset or 0
            day_offset = check.opt_int_param(day_of_week, "day_of_week", default=default)
        else:
            day_offset = 0

        return cron_schedule_from_schedule_type_and_offsets(
            schedule_type,
            minute_offset=minute_of_hour,
            hour_offset=hour_of_day or 0,
            day_offset=day_offset,
        )

    def _iterate_time_windows(
        self, start_timestamp: float, ignore_exclusions: bool = False
    ) -> Iterable[TimeWindow]:
        """Returns an infinite generator of time windows that start >= the given start time."""
        iterator = cron_string_iterator(
            start_timestamp=start_timestamp,
            cron_string=self.cron_schedule,
            execution_timezone=self.timezone,
        )
        curr_time = next(iterator)
        while curr_time.timestamp() < start_timestamp:
            curr_time = next(iterator)

        while True:
            next_time = next(iterator)
            if not self.is_window_start_excluded(curr_time) or ignore_exclusions:
                yield TimeWindow(curr_time, next_time)
            curr_time = next_time

    def _reverse_iterate_time_windows(
        self, end_timestamp: float, ignore_exclusions: bool = False
    ) -> Iterable[TimeWindow]:
        """Returns an infinite generator of time windows that end before the given end timestamp.
        For example, if you pass in any time on day N (including midnight) for a daily partition
        with offset 0 bounded at midnight, the first element this iterator will return is
        [day N-1, day N).

        If ignore_exclusions is True, excluded windows will be included in the iteration.  This is
        useful for checking for skipping excluded windows when calculating a schedule off of the
        time window partitions definition
        """
        iterator = reverse_cron_string_iterator(
            end_timestamp=end_timestamp,
            cron_string=self.cron_schedule,
            execution_timezone=self.timezone,
        )

        curr_time = next(iterator)
        while curr_time.timestamp() > end_timestamp:
            curr_time = next(iterator)

        while True:
            prev_time = next(iterator)
            if not self.is_window_start_excluded(prev_time) or ignore_exclusions:
                yield TimeWindow(prev_time, curr_time)
            curr_time = prev_time

    def get_partition_key_for_timestamp(self, timestamp: float, end_closed: bool = False) -> str:
        """Args:
        timestamp (float): Timestamp from the unix epoch, UTC.
        end_closed (bool): Whether the interval is closed at the end or at the beginning.
        """
        rev_iter = reverse_cron_string_iterator(timestamp, self.cron_schedule, self.timezone)
        prev_partition_key = None
        while prev_partition_key is None:
            prev_dt = next(rev_iter)
            if end_closed and prev_dt.timestamp() == timestamp:
                continue

            if self.is_window_start_excluded(prev_dt):
                continue

            prev_partition_key = dst_safe_strftime(
                prev_dt, self.timezone, self.fmt, self.cron_schedule
            )

        iterator = cron_string_iterator(timestamp, self.cron_schedule, self.timezone)
        next_partition_key = None
        next_dt = None
        while next_partition_key is None:
            next_dt = next(iterator)
            if self.is_window_start_excluded(next_dt):
                continue
            next_partition_key = dst_safe_strftime(
                next_dt, self.timezone, self.fmt, self.cron_schedule
            )

        if end_closed or (next_dt and next_dt.timestamp() > timestamp):
            return prev_partition_key
        else:
            return next_partition_key

    def less_than(self, partition_key1: str, partition_key2: str) -> bool:
        """Returns true if the partition_key1 is earlier than partition_key2."""
        return (
            self.start_time_for_partition_key(partition_key1).timestamp()
            < self.start_time_for_partition_key(partition_key2).timestamp()
        )

    @property
    def partitions_subset_class(self) -> type["TimeWindowPartitionsSubset"]:
        from dagster._core.definitions.partitions.subset.time_window import (
            TimeWindowPartitionsSubset,
        )

        return TimeWindowPartitionsSubset

    def subset_with_all_partitions(self) -> "PartitionsSubset":
        first_window = self.get_first_partition_window()
        last_window = self.get_last_partition_window()
        windows = (
            []
            if first_window is None or last_window is None
            else [TimeWindow(first_window.start, last_window.end)]
        )
        return self.partitions_subset_class(
            partitions_def=self, num_partitions=None, included_time_windows=windows
        )

    def get_serializable_unique_identifier(
        self, dynamic_partitions_store: Optional["DynamicPartitionsStore"] = None
    ) -> str:
        return hashlib.sha1(self.__repr__().encode("utf-8")).hexdigest()

    def has_partition_key(self, partition_key: str) -> bool:
        """Returns a boolean representing if the given partition key is valid."""
        try:
            partition_start_time = self.start_time_for_partition_key(partition_key)
            partition_start_timestamp = partition_start_time.timestamp()
        except ValueError:
            # unparseable partition key
            return False

        if self.is_window_start_excluded(partition_start_time):
            return False

        first_partition_window = self.get_first_partition_window()
        last_partition_window = self.get_last_partition_window()
        return not (
            # no partitions at all
            first_partition_window is None
            or last_partition_window is None
            # partition starts before the first valid partition
            or partition_start_timestamp < first_partition_window.start.timestamp()
            # partition starts after the last valid partition
            or partition_start_timestamp > last_partition_window.start.timestamp()
            # partition key string does not represent the start of an actual partition
            or dst_safe_strftime(partition_start_time, self.timezone, self.fmt, self.cron_schedule)
            != partition_key
        )

    def equal_except_for_start_or_end(self, other: "TimeWindowPartitionsDefinition") -> bool:
        """Returns True iff this is identical to other, except they're allowed to have different
        start and end datetimes.
        """
        return (
            self.timezone == other.timezone
            and self.fmt == other.fmt
            and self.cron_schedule == other.cron_schedule
            and self.end_offset == other.end_offset
            and self.exclusions == other.exclusions
        )

    def get_partition_key(self, key: Union[str, date, datetime]) -> str:
        if isinstance(key, date) or isinstance(key, datetime):
            key = key.strftime(self.fmt)

        # now should have str
        check.str_param(key, "key")
        if not self.has_partition_key(key):
            raise ValueError(f"Got invalid partition key {key!r}")

        return key

    @property
    def is_basic_daily(self) -> bool:
        return not self.exclusions and is_basic_daily(self.cron_schedule)

    @property
    def is_basic_hourly(self) -> bool:
        return not self.exclusions and is_basic_hourly(self.cron_schedule)
