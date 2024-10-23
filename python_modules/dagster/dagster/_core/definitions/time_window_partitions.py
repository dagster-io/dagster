import functools
import hashlib
import json
import re
from abc import abstractmethod, abstractproperty
from datetime import date, datetime, timedelta
from enum import Enum
from functools import cached_property
from typing import (
    AbstractSet,
    Any,
    Callable,
    FrozenSet,
    Iterable,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    cast,
)

import dagster._check as check
from dagster._annotations import PublicAttr, public
from dagster._core.definitions.partition import (
    DEFAULT_DATE_FORMAT,
    AllPartitionsSubset,
    PartitionedConfig,
    PartitionsDefinition,
    PartitionsSubset,
    ScheduleType,
    cron_schedule_from_schedule_type_and_offsets,
)
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.timestamp import TimestampWithTimezone
from dagster._core.errors import (
    DagsterInvalidDefinitionError,
    DagsterInvalidDeserializationVersionError,
    DagsterInvalidInvocationError,
)
from dagster._core.instance import DynamicPartitionsStore
from dagster._record import IHaveNew, record_custom
from dagster._serdes import whitelist_for_serdes
from dagster._serdes.serdes import NamedTupleSerializer
from dagster._time import (
    create_datetime,
    datetime_from_timestamp,
    get_current_timestamp,
    get_timezone,
)
from dagster._utils.cronstring import get_fixed_minute_interval, is_basic_daily, is_basic_hourly
from dagster._utils.partitions import DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE
from dagster._utils.schedules import (
    cron_string_iterator,
    cron_string_repeats_every_hour,
    is_valid_cron_schedule,
    reverse_cron_string_iterator,
)


def is_second_ambiguous_time(dt: datetime, tz: str):
    """Returns if a datetime is the second instance of an ambiguous time in the given timezone due
    to DST transitions. Assumes that dt is alraedy in the specified timezone.
    """
    # UTC is never ambiguous
    if tz.upper() == "UTC":
        return False

    # Ensure that the datetime is in the correct timezone
    tzinfo = check.not_none(dt.tzinfo)

    # Only interested in the second instance of an ambiguous time
    if dt.fold == 0:
        return False

    offset_before = cast(
        timedelta,
        (tzinfo.utcoffset(dt.replace(fold=0)) if dt.fold else tzinfo.utcoffset(dt)),
    )
    offset_after = cast(
        timedelta,
        (tzinfo.utcoffset(dt) if dt.fold else tzinfo.utcoffset(dt.replace(fold=1))),
    )
    return offset_before > offset_after


def dst_safe_fmt(fmt: str) -> str:
    """Adds UTC offset information to a datetime format string to disambiguate timestamps around DST
    transitions.
    """
    if "%z" in fmt:
        return fmt
    return fmt + "%z"


def dst_safe_strftime(dt: datetime, tz: str, fmt: str, cron_schedule: str) -> str:
    """A method for converting a datetime to a string which will append a suffix in cases where
    the resulting timestamp would be ambiguous due to DST transitions.

    Assumes that dt is already in the specified timezone.
    """
    # if the format already includes a UTC offset, then we don't need to do anything
    if "%z" in fmt:
        return dt.strftime(fmt)

    # only need to handle ambiguous times for cron schedules which repeat every hour
    if not cron_string_repeats_every_hour(cron_schedule):
        return dt.strftime(fmt)

    # if the datetime is the second instance of an ambiguous time, then we append the UTC offset
    if is_second_ambiguous_time(dt, tz):
        return dt.strftime(dst_safe_fmt(fmt))
    return dt.strftime(fmt)


def dst_safe_strptime(date_string: str, tz: str, fmt: str) -> datetime:
    """A method for parsing a datetime created with the dst_safe_strftime() method."""
    try:
        # first, try to parse the datetime in the normal format
        dt = datetime.strptime(date_string, fmt)
    except ValueError:
        # if this fails, try to parse the datetime with a UTC offset added
        dt = datetime.strptime(date_string, dst_safe_fmt(fmt))

    # the datetime object may have timezone information on it, depending on the format used. If it
    # does, we simply ensure that this timestamp is in the correct timezone.
    if dt.tzinfo:
        return datetime.fromtimestamp(dt.timestamp(), tz=get_timezone(tz))
    # otherwise, ensure that we assume the pre-transition timezone
    else:
        return create_datetime(
            year=dt.year,
            month=dt.month,
            day=dt.day,
            hour=dt.hour,
            minute=dt.minute,
            second=dt.second,
            microsecond=dt.microsecond,
            tz=get_timezone(tz),
            fold=0,
        )


class TimeWindow(NamedTuple):
    """An interval that is closed at the start and open at the end.

    Attributes:
        start (datetime): A datetime that marks the start of the window.
        end (datetime): A datetime that marks the end of the window.
    """

    start: PublicAttr[datetime]
    end: PublicAttr[datetime]


@whitelist_for_serdes(
    storage_name="TimeWindow",  # For back-compat with existing serdes
)
class PersistedTimeWindow(
    NamedTuple(
        "_PersistedTimeWindow", [("start", TimestampWithTimezone), ("end", TimestampWithTimezone)]
    )
):
    """Internal serialized representation of a time interval that is closed at the
    start and open at the end.
    """

    def __new__(
        cls,
        start: TimestampWithTimezone,
        end: TimestampWithTimezone,
    ):
        return super(cls, PersistedTimeWindow).__new__(
            cls,
            start=check.inst_param(start, "start", TimestampWithTimezone),
            end=check.inst_param(end, "end", TimestampWithTimezone),
        )

    @cached_property
    def start(self) -> datetime:
        start_timestamp_with_timezone = self._asdict()["start"]
        return datetime.fromtimestamp(
            start_timestamp_with_timezone.timestamp,
            tz=get_timezone(start_timestamp_with_timezone.timezone),
        )

    @cached_property
    def end(self) -> datetime:
        end_timestamp_with_timezone = self._asdict()["end"]
        return datetime.fromtimestamp(
            end_timestamp_with_timezone.timestamp,
            tz=get_timezone(end_timestamp_with_timezone.timezone),
        )

    @staticmethod
    def from_public_time_window(tw: TimeWindow, timezone: str):
        return PersistedTimeWindow(
            TimestampWithTimezone(tw.start.timestamp(), timezone),
            TimestampWithTimezone(tw.end.timestamp(), timezone),
        )

    def subtract(self, other: "PersistedTimeWindow") -> Sequence["PersistedTimeWindow"]:
        other_start_timestamp = other.start.timestamp()
        start_timestamp = self.start.timestamp()
        other_end_timestamp = other.end.timestamp()
        end_timestamp = self.end.timestamp()

        # Case where the two don't intersect at all - just return self
        # Note that this assumes end is exclusive
        if end_timestamp <= other_start_timestamp or other_end_timestamp <= start_timestamp:
            return [self]

        windows = []

        if other_start_timestamp > start_timestamp:
            windows.append(
                PersistedTimeWindow(start=self._asdict()["start"], end=other._asdict()["start"]),
            )

        if other_end_timestamp < end_timestamp:
            windows.append(
                PersistedTimeWindow(start=other._asdict()["end"], end=self._asdict()["end"])
            )

        return windows

    def to_public_time_window(self) -> TimeWindow:
        """Used for exposing TimeWindows over the public Dagster API."""
        return TimeWindow(start=self.start, end=self.end)


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

    We recommended limiting partition counts for each asset to 25,000 partitions or fewer.

    Args:
        cron_schedule (str): Determines the bounds of the time windows.
        start (datetime): The first partition in the set will start on at the first cron_schedule
            tick that is equal to or after this value.
        timezone (Optional[str]): The timezone in which each time should exist.
            Supported strings for timezones are the ones provided by the
            `IANA time zone database <https://www.iana.org/time-zones>` - e.g. "America/Los_Angeles".

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
    """

    start_ts: TimestampWithTimezone
    timezone: PublicAttr[str]
    end_ts: Optional[TimestampWithTimezone]
    fmt: PublicAttr[str]
    end_offset: PublicAttr[int]
    cron_schedule: PublicAttr[str]

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

        return super().__new__(
            cls,
            start_ts=start,
            timezone=timezone,
            end_ts=end,
            fmt=fmt,
            end_offset=end_offset,
            cron_schedule=cron_schedule,
        )

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

    def _get_current_timestamp(self, current_time: Optional[datetime]) -> float:
        if not current_time:
            return get_current_timestamp()

        # if a naive current time was passed in, assume it was the same timezone as the partition set
        if not current_time.tzinfo:
            current_time = current_time.replace(tzinfo=get_timezone(self.timezone))

        return current_time.timestamp()

    def get_num_partitions_in_window(self, time_window: TimeWindow) -> int:
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
        if fixed_minute_interval:
            minutes_in_window = (time_window.end.timestamp() - time_window.start.timestamp()) / 60
            return int(minutes_in_window // fixed_minute_interval)

        return len(self.get_partition_keys_in_time_window(time_window))

    def get_num_partitions(
        self,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> int:
        last_partition_window = self.get_last_partition_window(current_time)
        first_partition_window = self.get_first_partition_window(current_time)

        if not last_partition_window or not first_partition_window:
            return 0

        return self.get_num_partitions_in_window(
            TimeWindow(start=first_partition_window.start, end=last_partition_window.end)
        )

    def get_partition_keys_between_indexes(
        self, start_idx: int, end_idx: int, current_time: Optional[datetime] = None
    ) -> List[str]:
        # Fetches the partition keys between the given start and end indices.
        # Start index is inclusive, end index is exclusive.
        # Method added for performance reasons, to only string format
        # partition keys included within the indices.
        current_timestamp = self._get_current_timestamp(current_time=current_time)

        partitions_past_current_time = 0
        partition_keys = []
        reached_end = False

        for idx, time_window in enumerate(self._iterate_time_windows(self.start.timestamp())):
            if time_window.end.timestamp() >= current_timestamp:
                reached_end = True
            if self.end and time_window.end.timestamp() > self.end.timestamp():
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

    def get_partition_keys(
        self,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> Sequence[str]:
        current_timestamp = self._get_current_timestamp(current_time=current_time)

        partitions_past_current_time = 0
        partition_keys: List[str] = []
        for time_window in self._iterate_time_windows(self.start.timestamp()):
            if self.end and time_window.end.timestamp() > self.end.timestamp():
                break
            if (
                time_window.end.timestamp() <= current_timestamp
                or partitions_past_current_time < self.end_offset
            ):
                partition_keys.append(
                    dst_safe_strftime(
                        time_window.start, self.timezone, self.fmt, self.cron_schedule
                    )
                )

                if time_window.end.timestamp() > current_timestamp:
                    partitions_past_current_time += 1
            else:
                break

        if self.end_offset < 0:
            partition_keys = partition_keys[: self.end_offset]

        return partition_keys

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
        return (
            f"TimeWindowPartitionsDefinition(start={self.start.timestamp()},"
            f" end={self.end.timestamp() if self.end else None},"
            f" timezone='{self.timezone}', fmt='{self.fmt}', end_offset={self.end_offset},"
            f" cron_schedule='{self.cron_schedule}')"
        )

    def __hash__(self):
        return hash(tuple(self.__repr__()))

    @functools.lru_cache(maxsize=100)
    def time_window_for_partition_key(self, partition_key: str) -> TimeWindow:
        partition_key_dt = dst_safe_strptime(partition_key, self.timezone, self.fmt)
        return next(iter(self._iterate_time_windows(partition_key_dt.timestamp())))

    @functools.lru_cache(maxsize=5)
    def time_windows_for_partition_keys(
        self,
        partition_keys: FrozenSet[str],
        validate: bool = True,
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
        partition_key_time_windows: List[TimeWindow] = []
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

    def get_next_partition_key(
        self, partition_key: str, current_time: Optional[datetime] = None
    ) -> Optional[str]:
        last_partition_window = self.get_last_partition_window(current_time)
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
        self, end_dt: datetime, current_time: Optional[datetime] = None, respect_bounds: bool = True
    ) -> Optional[TimeWindow]:
        windows_iter = iter(self._iterate_time_windows(end_dt.timestamp()))
        next_window = next(windows_iter)

        if respect_bounds:
            last_partition_window = self.get_last_partition_window(current_time)
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
    def _get_first_partition_window(self, *, current_timestamp: float) -> Optional[TimeWindow]:
        time_window = next(iter(self._iterate_time_windows(self.start.timestamp())))

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

    def get_first_partition_window(
        self, current_time: Optional[datetime] = None
    ) -> Optional[TimeWindow]:
        current_timestamp = self._get_current_timestamp(current_time)
        return self._get_first_partition_window(current_timestamp=current_timestamp)

    @functools.lru_cache(maxsize=256)
    def _get_last_partition_window(self, *, current_timestamp: float) -> Optional[TimeWindow]:
        if self._get_first_partition_window(current_timestamp=current_timestamp) is None:
            return None

        if self.end and self.end.timestamp() < current_timestamp:
            current_timestamp = self.end.timestamp()

        if self.end_offset == 0:
            return next(iter(self._reverse_iterate_time_windows(current_timestamp)))
        else:
            # TODO: make this efficient
            last_partition_key = super().get_last_partition_key(
                datetime.fromtimestamp(current_timestamp, tz=get_timezone(self.timezone))
            )
            return (
                self.time_window_for_partition_key(last_partition_key)
                if last_partition_key
                else None
            )

    def get_last_partition_window(
        self, current_time: Optional[datetime] = None
    ) -> Optional[TimeWindow]:
        current_timestamp = self._get_current_timestamp(current_time)
        return self._get_last_partition_window(current_timestamp=current_timestamp)

    def get_first_partition_key(
        self,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> Optional[str]:
        first_window = self.get_first_partition_window(current_time)
        if first_window is None:
            return None

        return dst_safe_strftime(first_window.start, self.timezone, self.fmt, self.cron_schedule)

    def get_last_partition_key(
        self,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> Optional[str]:
        last_window = self.get_last_partition_window(current_time)
        if last_window is None:
            return None

        return dst_safe_strftime(last_window.start, self.timezone, self.fmt, self.cron_schedule)

    def end_time_for_partition_key(self, partition_key: str) -> datetime:
        return self.time_window_for_partition_key(partition_key).end

    @functools.lru_cache(maxsize=5)
    def get_partition_keys_in_time_window(self, time_window: TimeWindow) -> Sequence[str]:
        result: List[str] = []
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

    def get_partition_key_range_for_time_window(self, time_window: TimeWindow) -> PartitionKeyRange:
        start_partition_key = self.get_partition_key_for_timestamp(time_window.start.timestamp())
        end_partition_key = self.get_partition_key_for_timestamp(
            check.not_none(self.get_prev_partition_window(time_window.end)).start.timestamp()
        )

        return PartitionKeyRange(start_partition_key, end_partition_key)

    def get_partition_keys_in_range(
        self,
        partition_key_range: PartitionKeyRange,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> Sequence[str]:
        start_time = self.start_time_for_partition_key(partition_key_range.start)
        if not (start_time.timestamp() >= self.start.timestamp()):
            raise DagsterInvalidInvocationError(
                f"Partition key range start {partition_key_range.start} is before "
                f"the partitions definition start time {self.start}"
            )
        end_time = self.end_time_for_partition_key(partition_key_range.end)
        if self.end:
            if not (end_time.timestamp() <= self.end.timestamp()):
                raise DagsterInvalidInvocationError(
                    f"Partition key range end {partition_key_range.end} is after the "
                    f"partitions definition end time {self.end}"
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
            int,
            check.opt_int_param(minute_of_hour, "minute_of_hour", default=self.minute_offset),
        )

        if schedule_type == ScheduleType.HOURLY:
            check.invariant(
                hour_of_day is None, "Cannot set hour parameter with hourly partitions."
            )
        else:
            hour_of_day = cast(
                int, check.opt_int_param(hour_of_day, "hour_of_day", default=self.hour_offset)
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

    def _iterate_time_windows(self, start_timestamp: float) -> Iterable[TimeWindow]:
        """Returns an infinite generator of time windows that start after the given start time."""
        iterator = cron_string_iterator(
            start_timestamp=start_timestamp,
            cron_string=self.cron_schedule,
            execution_timezone=self.timezone,
        )
        prev_time = next(iterator)
        while prev_time.timestamp() < start_timestamp:
            prev_time = next(iterator)

        while True:
            next_time = next(iterator)
            yield TimeWindow(prev_time, next_time)
            prev_time = next_time

    def _reverse_iterate_time_windows(self, end_timestamp: float) -> Iterable[TimeWindow]:
        """Returns an infinite generator of time windows that end before the given end time."""
        iterator = reverse_cron_string_iterator(
            end_timestamp=end_timestamp,
            cron_string=self.cron_schedule,
            execution_timezone=self.timezone,
        )

        prev_time = next(iterator)
        while prev_time.timestamp() > end_timestamp:
            prev_time = next(iterator)

        while True:
            next_time = next(iterator)
            yield TimeWindow(next_time, prev_time)
            prev_time = next_time

    def get_partition_key_for_timestamp(self, timestamp: float, end_closed: bool = False) -> str:
        """Args:
        timestamp (float): Timestamp from the unix epoch, UTC.
        end_closed (bool): Whether the interval is closed at the end or at the beginning.
        """
        iterator = cron_string_iterator(
            timestamp, self.cron_schedule, self.timezone, start_offset=-1
        )
        # prev will be < timestamp
        prev = next(iterator)
        # prev_next will be >= timestamp
        prev_next = next(iterator)

        if end_closed or prev_next.timestamp() > timestamp:
            return dst_safe_strftime(prev, self.timezone, self.fmt, self.cron_schedule)
        else:
            return dst_safe_strftime(prev_next, self.timezone, self.fmt, self.cron_schedule)

    def less_than(self, partition_key1: str, partition_key2: str) -> bool:
        """Returns true if the partition_key1 is earlier than partition_key2."""
        return (
            self.start_time_for_partition_key(partition_key1).timestamp()
            < self.start_time_for_partition_key(partition_key2).timestamp()
        )

    @property
    def partitions_subset_class(self) -> Type["PartitionsSubset"]:
        return PartitionKeysTimeWindowPartitionsSubset

    def empty_subset(self) -> "PartitionsSubset":
        return self.partitions_subset_class.empty_subset(self)

    def subset_with_all_partitions(
        self,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> "PartitionsSubset":
        first_window = self.get_first_partition_window(current_time)
        last_window = self.get_last_partition_window(current_time)
        windows = (
            []
            if first_window is None or last_window is None
            else [TimeWindow(first_window.start, last_window.end)]
        )
        return TimeWindowPartitionsSubset(
            partitions_def=self, num_partitions=None, included_time_windows=windows
        )

    def get_serializable_unique_identifier(
        self, dynamic_partitions_store: Optional[DynamicPartitionsStore] = None
    ) -> str:
        return hashlib.sha1(self.__repr__().encode("utf-8")).hexdigest()

    def has_partition_key(
        self,
        partition_key: str,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> bool:
        """Returns a boolean representing if the given partition key is valid."""
        try:
            partition_start_time = self.start_time_for_partition_key(partition_key)
            partition_start_timestamp = partition_start_time.timestamp()
        except ValueError:
            # unparseable partition key
            return False

        first_partition_window = self.get_first_partition_window(current_time=current_time)
        last_partition_window = self.get_last_partition_window(current_time=current_time)
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
        )

    @property
    def is_basic_daily(self) -> bool:
        return is_basic_daily(self.cron_schedule)

    @property
    def is_basic_hourly(self) -> bool:
        return is_basic_hourly(self.cron_schedule)


class DailyPartitionsDefinition(TimeWindowPartitionsDefinition):
    """A set of daily partitions.

    The first partition in the set will start at the start_date at midnight. The last partition
    in the set will end before the current time, unless the end_offset argument is set to a
    positive number. If minute_offset and/or hour_offset are used, the start and end times of
    each partition will be hour_offset:minute_offset of each day.

    Args:
        start_date (Union[datetime.datetime, str]): The first date in the set of partitions. Can
            provide in either a datetime or string format.
        end_date (Union[datetime.datetime, str, None]): The last date(excluding) in the set of partitions.
            Default is None. Can provide in either a datetime or string format.
        minute_offset (int): Number of minutes past the hour to "split" the partition. Defaults
            to 0.
        hour_offset (int): Number of hours past 00:00 to "split" the partition. Defaults to 0.
        timezone (Optional[str]): The timezone in which each date should exist.
            Supported strings for timezones are the ones provided by the
            `IANA time zone database <https://www.iana.org/time-zones>` - e.g. "America/Los_Angeles".
        fmt (Optional[str]): The date format to use. Defaults to `%Y-%m-%d`.
        end_offset (int): Extends the partition set by a number of partitions equal to the value
            passed. If end_offset is 0 (the default), the last partition ends before the current
            time. If end_offset is 1, the second-to-last partition ends before the current time,
            and so on.

    .. code-block:: python

        DailyPartitionsDefinition(start_date="2022-03-12")
        # creates partitions (2022-03-12-00:00, 2022-03-13-00:00), (2022-03-13-00:00, 2022-03-14-00:00), ...

        DailyPartitionsDefinition(start_date="2022-03-12", minute_offset=15, hour_offset=16)
        # creates partitions (2022-03-12-16:15, 2022-03-13-16:15), (2022-03-13-16:15, 2022-03-14-16:15), ...
    """

    # mapping for fields defined on TimeWindowPartitionsDefinition to this subclasses __new__
    __field_remap__ = {
        "start_ts": "start_date",
        "end_ts": "end_date",
    }

    def __new__(
        cls,
        start_date: Union[datetime, str],
        end_date: Union[datetime, str, None] = None,
        minute_offset: int = 0,
        hour_offset: int = 0,
        timezone: Optional[str] = None,
        fmt: Optional[str] = None,
        end_offset: int = 0,
        **kwargs,
    ):
        _fmt = fmt or DEFAULT_DATE_FORMAT

        schedule_type = ScheduleType.DAILY

        # We accept cron_schedule "hidden" via kwargs to support record copy()
        cron_schedule = kwargs.get("cron_schedule")
        if cron_schedule:
            schedule_type = None

        return super(DailyPartitionsDefinition, cls).__new__(
            cls,
            schedule_type=schedule_type,
            start=start_date,
            end=end_date,
            minute_offset=minute_offset,
            hour_offset=hour_offset,
            timezone=timezone,
            fmt=_fmt,
            end_offset=end_offset,
            cron_schedule=cron_schedule,
        )


def wrap_time_window_run_config_fn(
    run_config_fn: Optional[Callable[[datetime, datetime], Mapping[str, Any]]],
    partitions_def: TimeWindowPartitionsDefinition,
) -> Callable[[str], Mapping[str, Any]]:
    def _run_config_wrapper(key: str) -> Mapping[str, Any]:
        if not run_config_fn:
            return {}
        time_window = partitions_def.time_window_for_partition_key(key)
        return run_config_fn(time_window.start, time_window.end)

    return _run_config_wrapper


def wrap_time_window_tags_fn(
    tags_fn: Optional[Callable[[datetime, datetime], Mapping[str, str]]],
    partitions_def: TimeWindowPartitionsDefinition,
) -> Callable[[str], Mapping[str, str]]:
    def _tag_wrapper(key: str) -> Mapping[str, str]:
        if not tags_fn:
            return {}
        time_window = partitions_def.time_window_for_partition_key(key)
        return tags_fn(time_window.start, time_window.end)

    return _tag_wrapper


def daily_partitioned_config(
    start_date: Union[datetime, str],
    minute_offset: int = 0,
    hour_offset: int = 0,
    timezone: Optional[str] = None,
    fmt: Optional[str] = None,
    end_offset: int = 0,
    tags_for_partition_fn: Optional[Callable[[datetime, datetime], Mapping[str, str]]] = None,
) -> Callable[
    [Callable[[datetime, datetime], Mapping[str, Any]]],
    PartitionedConfig[DailyPartitionsDefinition],
]:
    """Defines run config over a set of daily partitions.

    The decorated function should accept a start datetime and end datetime, which represent the bounds
    of the date partition the config should delineate.

    The decorated function should return a run config dictionary.

    The resulting object created by this decorator can be provided to the config argument of a Job.
    The first partition in the set will start at the start_date at midnight. The last partition in
    the set will end before the current time, unless the end_offset argument is set to a positive
    number. If minute_offset and/or hour_offset are used, the start and end times of each partition
    will be hour_offset:minute_offset of each day.

    Args:
        start_date (Union[datetime.datetime, str]): The first date in the set of partitions. Can
            provide in either a datetime or string format.
        minute_offset (int): Number of minutes past the hour to "split" the partition. Defaults
            to 0.
        hour_offset (int): Number of hours past 00:00 to "split" the partition. Defaults to 0.
        timezone (Optional[str]): The timezone in which each date should exist.
            Supported strings for timezones are the ones provided by the
            `IANA time zone database <https://www.iana.org/time-zones>` - e.g. "America/Los_Angeles".
        fmt (Optional[str]): The date format to use. Defaults to `%Y-%m-%d`.
        end_offset (int): Extends the partition set by a number of partitions equal to the value
            passed. If end_offset is 0 (the default), the last partition ends before the current
            time. If end_offset is 1, the second-to-last partition ends before the current time,
            and so on.
        tags_for_partition_fn (Optional[Callable[[str], Mapping[str, str]]]): A function that
            accepts a partition time window and returns a dictionary of tags to attach to runs for
            that partition.

    .. code-block:: python

        @daily_partitioned_config(start_date="2022-03-12")
        # creates partitions (2022-03-12-00:00, 2022-03-13-00:00), (2022-03-13-00:00, 2022-03-14-00:00), ...

        @daily_partitioned_config(start_date="2022-03-12", minute_offset=15, hour_offset=16)
        # creates partitions (2022-03-12-16:15, 2022-03-13-16:15), (2022-03-13-16:15, 2022-03-14-16:15), ...
    """

    def inner(
        fn: Callable[[datetime, datetime], Mapping[str, Any]],
    ) -> PartitionedConfig[DailyPartitionsDefinition]:
        check.callable_param(fn, "fn")

        partitions_def = DailyPartitionsDefinition(
            start_date=start_date,
            minute_offset=minute_offset,
            hour_offset=hour_offset,
            timezone=timezone,
            fmt=fmt,
            end_offset=end_offset,
        )

        return PartitionedConfig(
            run_config_for_partition_key_fn=wrap_time_window_run_config_fn(fn, partitions_def),
            partitions_def=partitions_def,
            decorated_fn=fn,
            tags_for_partition_key_fn=wrap_time_window_tags_fn(
                tags_for_partition_fn, partitions_def
            ),
        )

    return inner


class HourlyPartitionsDefinition(TimeWindowPartitionsDefinition):
    """A set of hourly partitions.

    The first partition in the set will start on the start_date at midnight. The last partition
    in the set will end before the current time, unless the end_offset argument is set to a
    positive number. If minute_offset is provided, the start and end times of each partition
    will be minute_offset past the hour.

    Args:
        start_date (Union[datetime.datetime, str]): The first date in the set of partitions. Can
            provide in either a datetime or string format.
        end_date (Union[datetime.datetime, str, None]): The last date(excluding) in the set of partitions.
            Default is None. Can provide in either a datetime or string format.
        minute_offset (int): Number of minutes past the hour to "split" the partition. Defaults
            to 0.
        fmt (Optional[str]): The date format to use. Defaults to `%Y-%m-%d`. Note that if a non-UTC
            timezone is used, the date format must include a timezone offset to disambiguate between
            multiple instances of the same time before and after the Fall DST transition. If the
            format does not contain this offset, the second instance of the ambiguous time partition
            key will have the UTC offset automatically appended to it.
        timezone (Optional[str]): The timezone in which each date should exist.
            Supported strings for timezones are the ones provided by the
            `IANA time zone database <https://www.iana.org/time-zones>` - e.g. "America/Los_Angeles".
        end_offset (int): Extends the partition set by a number of partitions equal to the value
            passed. If end_offset is 0 (the default), the last partition ends before the current
            time. If end_offset is 1, the second-to-last partition ends before the current time,
            and so on.

    .. code-block:: python

        HourlyPartitionsDefinition(start_date=datetime(2022, 03, 12))
        # creates partitions (2022-03-12-00:00, 2022-03-12-01:00), (2022-03-12-01:00, 2022-03-12-02:00), ...

        HourlyPartitionsDefinition(start_date=datetime(2022, 03, 12), minute_offset=15)
        # creates partitions (2022-03-12-00:15, 2022-03-12-01:15), (2022-03-12-01:15, 2022-03-12-02:15), ...
    """

    # mapping for fields defined on TimeWindowPartitionsDefinition to this subclasses __new__
    __field_remap__ = {
        "start_ts": "start_date",
        "end_ts": "end_date",
    }

    def __new__(
        cls,
        start_date: Union[datetime, str],
        end_date: Union[datetime, str, None] = None,
        minute_offset: int = 0,
        timezone: Optional[str] = None,
        fmt: Optional[str] = None,
        end_offset: int = 0,
        **kwargs,
    ):
        _fmt = fmt or DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE
        schedule_type = ScheduleType.HOURLY

        # We accept cron_schedule "hidden" via kwargs to support record copy()
        cron_schedule = kwargs.get("cron_schedule")
        if cron_schedule:
            schedule_type = None

        return super(HourlyPartitionsDefinition, cls).__new__(
            cls,
            schedule_type=schedule_type,
            start=start_date,
            end=end_date,
            minute_offset=minute_offset,
            timezone=timezone,
            fmt=_fmt,
            end_offset=end_offset,
            cron_schedule=cron_schedule,
        )


def hourly_partitioned_config(
    start_date: Union[datetime, str],
    minute_offset: int = 0,
    timezone: Optional[str] = None,
    fmt: Optional[str] = None,
    end_offset: int = 0,
    tags_for_partition_fn: Optional[Callable[[datetime, datetime], Mapping[str, str]]] = None,
) -> Callable[
    [Callable[[datetime, datetime], Mapping[str, Any]]],
    PartitionedConfig[HourlyPartitionsDefinition],
]:
    """Defines run config over a set of hourly partitions.

    The decorated function should accept a start datetime and end datetime, which represent the date
    partition the config should delineate.

    The decorated function should return a run config dictionary.

    The resulting object created by this decorator can be provided to the config argument of a Job.
    The first partition in the set will start at the start_date at midnight. The last partition in
    the set will end before the current time, unless the end_offset argument is set to a positive
    number. If minute_offset is provided, the start and end times of each partition will be
    minute_offset past the hour.

    Args:
        start_date (Union[datetime.datetime, str]): The first date in the set of partitions. Can
            provide in either a datetime or string format.
        minute_offset (int): Number of minutes past the hour to "split" the partition. Defaults
            to 0.
        fmt (Optional[str]): The date format to use. Defaults to `%Y-%m-%d`.
        timezone (Optional[str]): The timezone in which each date should exist.
            Supported strings for timezones are the ones provided by the
            `IANA time zone database <https://www.iana.org/time-zones>` - e.g. "America/Los_Angeles".
        end_offset (int): Extends the partition set by a number of partitions equal to the value
            passed. If end_offset is 0 (the default), the last partition ends before the current
            time. If end_offset is 1, the second-to-last partition ends before the current time,
            and so on.
        tags_for_partition_fn (Optional[Callable[[str], Mapping[str, str]]]): A function that
            accepts a partition time window and returns a dictionary of tags to attach to runs for
            that partition.

    .. code-block:: python

        @hourly_partitioned_config(start_date=datetime(2022, 03, 12))
        # creates partitions (2022-03-12-00:00, 2022-03-12-01:00), (2022-03-12-01:00, 2022-03-12-02:00), ...

        @hourly_partitioned_config(start_date=datetime(2022, 03, 12), minute_offset=15)
        # creates partitions (2022-03-12-00:15, 2022-03-12-01:15), (2022-03-12-01:15, 2022-03-12-02:15), ...
    """

    def inner(
        fn: Callable[[datetime, datetime], Mapping[str, Any]],
    ) -> PartitionedConfig[HourlyPartitionsDefinition]:
        check.callable_param(fn, "fn")

        partitions_def = HourlyPartitionsDefinition(
            start_date=start_date,
            minute_offset=minute_offset,
            timezone=timezone,
            fmt=fmt,
            end_offset=end_offset,
        )
        return PartitionedConfig(
            run_config_for_partition_key_fn=wrap_time_window_run_config_fn(fn, partitions_def),
            partitions_def=partitions_def,
            decorated_fn=fn,
            tags_for_partition_key_fn=wrap_time_window_tags_fn(
                tags_for_partition_fn, partitions_def
            ),
        )

    return inner


class MonthlyPartitionsDefinition(TimeWindowPartitionsDefinition):
    """A set of monthly partitions.

    The first partition in the set will start at the soonest first of the month after start_date
    at midnight. The last partition in the set will end before the current time, unless the
    end_offset argument is set to a positive number. If day_offset is provided, the start and
    end date of each partition will be day_offset. If minute_offset and/or hour_offset are used,
    the start and end times of each partition will be hour_offset:minute_offset of each day.

    Args:
        start_date (Union[datetime.datetime, str]): The first date in the set of partitions will be
            midnight the soonest first of the month following start_date. Can provide in either a
            datetime or string format.
        end_date (Union[datetime.datetime, str, None]): The last date(excluding) in the set of partitions.
            Default is None. Can provide in either a datetime or string format.
        minute_offset (int): Number of minutes past the hour to "split" the partition. Defaults
            to 0.
        hour_offset (int): Number of hours past 00:00 to "split" the partition. Defaults to 0.
        day_offset (int): Day of the month to "split" the partition. Defaults to 1.
        timezone (Optional[str]): The timezone in which each date should exist.
            Supported strings for timezones are the ones provided by the
            `IANA time zone database <https://www.iana.org/time-zones>` - e.g. "America/Los_Angeles".
        fmt (Optional[str]): The date format to use. Defaults to `%Y-%m-%d`.
        end_offset (int): Extends the partition set by a number of partitions equal to the value
            passed. If end_offset is 0 (the default), the last partition ends before the current
            time. If end_offset is 1, the second-to-last partition ends before the current time,
            and so on.

    .. code-block:: python

        MonthlyPartitionsDefinition(start_date="2022-03-12")
        # creates partitions (2022-04-01-00:00, 2022-05-01-00:00), (2022-05-01-00:00, 2022-06-01-00:00), ...

        MonthlyPartitionsDefinition(start_date="2022-03-12", minute_offset=15, hour_offset=3, day_offset=5)
        # creates partitions (2022-04-05-03:15, 2022-05-05-03:15), (2022-05-05-03:15, 2022-06-05-03:15), ...
    """

    # mapping for fields defined on TimeWindowPartitionsDefinition to this subclasses __new__
    __field_remap__ = {
        "start_ts": "start_date",
        "end_ts": "end_date",
    }

    def __new__(
        cls,
        start_date: Union[datetime, str],
        end_date: Union[datetime, str, None] = None,
        minute_offset: int = 0,
        hour_offset: int = 0,
        day_offset: int = 1,
        timezone: Optional[str] = None,
        fmt: Optional[str] = None,
        end_offset: int = 0,
        **kwargs,
    ):
        _fmt = fmt or DEFAULT_DATE_FORMAT
        schedule_type = ScheduleType.MONTHLY

        # We accept cron_schedule "hidden" via kwargs to support record copy()
        cron_schedule = kwargs.get("cron_schedule")
        if cron_schedule:
            schedule_type = None
            check.invariant(
                day_offset == 1,
                f"Reconstruction by cron_schedule got unexpected day_offset {day_offset}, expected 1.",
            )
            day_offset = 0

        return super(MonthlyPartitionsDefinition, cls).__new__(
            cls,
            schedule_type=schedule_type,
            start=start_date,
            end=end_date,
            minute_offset=minute_offset,
            hour_offset=hour_offset,
            day_offset=day_offset,
            timezone=timezone,
            fmt=_fmt,
            end_offset=end_offset,
            cron_schedule=cron_schedule,
        )


def monthly_partitioned_config(
    start_date: Union[datetime, str],
    minute_offset: int = 0,
    hour_offset: int = 0,
    day_offset: int = 1,
    timezone: Optional[str] = None,
    fmt: Optional[str] = None,
    end_offset: int = 0,
    tags_for_partition_fn: Optional[Callable[[datetime, datetime], Mapping[str, str]]] = None,
) -> Callable[
    [Callable[[datetime, datetime], Mapping[str, Any]]],
    PartitionedConfig[MonthlyPartitionsDefinition],
]:
    """Defines run config over a set of monthly partitions.

    The decorated function should accept a start datetime and end datetime, which represent the date
    partition the config should delineate.

    The decorated function should return a run config dictionary.

    The resulting object created by this decorator can be provided to the config argument of a Job.
    The first partition in the set will start at midnight on the soonest first of the month after
    start_date. The last partition in the set will end before the current time, unless the
    end_offset argument is set to a positive number. If day_offset is provided, the start and end
    date of each partition will be day_offset. If minute_offset and/or hour_offset are used, the
    start and end times of each partition will be hour_offset:minute_offset of each day.

    Args:
        start_date (Union[datetime.datetime, str]): The first date in the set of partitions will be
            midnight the soonest first of the month following start_date. Can provide in either a
            datetime or string format.
        minute_offset (int): Number of minutes past the hour to "split" the partition. Defaults
            to 0.
        hour_offset (int): Number of hours past 00:00 to "split" the partition. Defaults to 0.
        day_offset (int): Day of the month to "split" the partition. Defaults to 1.
        timezone (Optional[str]): The timezone in which each date should exist.
            Supported strings for timezones are the ones provided by the
            `IANA time zone database <https://www.iana.org/time-zones>` - e.g. "America/Los_Angeles".
        fmt (Optional[str]): The date format to use. Defaults to `%Y-%m-%d`.
        end_offset (int): Extends the partition set by a number of partitions equal to the value
            passed. If end_offset is 0 (the default), the last partition ends before the current
            time. If end_offset is 1, the second-to-last partition ends before the current time,
            and so on.
        tags_for_partition_fn (Optional[Callable[[str], Mapping[str, str]]]): A function that
            accepts a partition time window and returns a dictionary of tags to attach to runs for
            that partition.

    .. code-block:: python

        @monthly_partitioned_config(start_date="2022-03-12")
        # creates partitions (2022-04-01-00:00, 2022-05-01-00:00), (2022-05-01-00:00, 2022-06-01-00:00), ...

        @monthly_partitioned_config(start_date="2022-03-12", minute_offset=15, hour_offset=3, day_offset=5)
        # creates partitions (2022-04-05-03:15, 2022-05-05-03:15), (2022-05-05-03:15, 2022-06-05-03:15), ...
    """

    def inner(
        fn: Callable[[datetime, datetime], Mapping[str, Any]],
    ) -> PartitionedConfig[MonthlyPartitionsDefinition]:
        check.callable_param(fn, "fn")

        partitions_def = MonthlyPartitionsDefinition(
            start_date=start_date,
            minute_offset=minute_offset,
            hour_offset=hour_offset,
            day_offset=day_offset,
            timezone=timezone,
            fmt=fmt,
            end_offset=end_offset,
        )

        return PartitionedConfig(
            run_config_for_partition_key_fn=wrap_time_window_run_config_fn(fn, partitions_def),
            partitions_def=partitions_def,
            decorated_fn=fn,
            tags_for_partition_key_fn=wrap_time_window_tags_fn(
                tags_for_partition_fn, partitions_def
            ),
        )

    return inner


class WeeklyPartitionsDefinition(TimeWindowPartitionsDefinition):
    """Defines a set of weekly partitions.

    The first partition in the set will start at the start_date. The last partition in the set will
    end before the current time, unless the end_offset argument is set to a positive number. If
    day_offset is provided, the start and end date of each partition will be day of the week
    corresponding to day_offset (0 indexed with Sunday as the start of the week). If
    minute_offset and/or hour_offset are used, the start and end times of each partition will be
    hour_offset:minute_offset of each day.

    Args:
        start_date (Union[datetime.datetime, str]): The first date in the set of partitions will
            Sunday at midnight following start_date. Can provide in either a datetime or string
            format.
        end_date (Union[datetime.datetime, str, None]): The last date(excluding) in the set of partitions.
            Default is None. Can provide in either a datetime or string format.
        minute_offset (int): Number of minutes past the hour to "split" the partition. Defaults
            to 0.
        hour_offset (int): Number of hours past 00:00 to "split" the partition. Defaults to 0.
        day_offset (int): Day of the week to "split" the partition. Defaults to 0 (Sunday).
        timezone (Optional[str]): The timezone in which each date should exist.
            Supported strings for timezones are the ones provided by the
            `IANA time zone database <https://www.iana.org/time-zones>` - e.g. "America/Los_Angeles".
        fmt (Optional[str]): The date format to use. Defaults to `%Y-%m-%d`.
        end_offset (int): Extends the partition set by a number of partitions equal to the value
            passed. If end_offset is 0 (the default), the last partition ends before the current
            time. If end_offset is 1, the second-to-last partition ends before the current time,
            and so on.

    .. code-block:: python

        WeeklyPartitionsDefinition(start_date="2022-03-12")
        # creates partitions (2022-03-13-00:00, 2022-03-20-00:00), (2022-03-20-00:00, 2022-03-27-00:00), ...

        WeeklyPartitionsDefinition(start_date="2022-03-12", minute_offset=15, hour_offset=3, day_offset=6)
        # creates partitions (2022-03-12-03:15, 2022-03-19-03:15), (2022-03-19-03:15, 2022-03-26-03:15), ...
    """

    # mapping for fields defined on TimeWindowPartitionsDefinition to this subclasses __new__
    __field_remap__ = {
        "start_ts": "start_date",
        "end_ts": "end_date",
    }

    def __new__(
        cls,
        start_date: Union[datetime, str],
        end_date: Union[datetime, str, None] = None,
        minute_offset: int = 0,
        hour_offset: int = 0,
        day_offset: int = 0,
        timezone: Optional[str] = None,
        fmt: Optional[str] = None,
        end_offset: int = 0,
        **kwargs,
    ):
        _fmt = fmt or DEFAULT_DATE_FORMAT
        schedule_type = ScheduleType.WEEKLY
        # We accept cron_schedule "hidden" via kwargs to support record copy()
        cron_schedule = kwargs.get("cron_schedule")
        if cron_schedule:
            schedule_type = None

        return super(WeeklyPartitionsDefinition, cls).__new__(
            cls,
            schedule_type=schedule_type,
            start=start_date,
            end=end_date,
            minute_offset=minute_offset,
            hour_offset=hour_offset,
            day_offset=day_offset,
            timezone=timezone,
            fmt=_fmt,
            end_offset=end_offset,
            cron_schedule=cron_schedule,
        )


def weekly_partitioned_config(
    start_date: Union[datetime, str],
    minute_offset: int = 0,
    hour_offset: int = 0,
    day_offset: int = 0,
    timezone: Optional[str] = None,
    fmt: Optional[str] = None,
    end_offset: int = 0,
    tags_for_partition_fn: Optional[Callable[[datetime, datetime], Mapping[str, str]]] = None,
) -> Callable[
    [Callable[[datetime, datetime], Mapping[str, Any]]],
    PartitionedConfig[WeeklyPartitionsDefinition],
]:
    """Defines run config over a set of weekly partitions.

    The decorated function should accept a start datetime and end datetime, which represent the date
    partition the config should delineate.

    The decorated function should return a run config dictionary.

    The resulting object created by this decorator can be provided to the config argument of a Job.
    The first partition in the set will start at the start_date. The last partition in the set will
    end before the current time, unless the end_offset argument is set to a positive number. If
    day_offset is provided, the start and end date of each partition will be day of the week
    corresponding to day_offset (0 indexed with Sunday as the start of the week). If
    minute_offset and/or hour_offset are used, the start and end times of each partition will be
    hour_offset:minute_offset of each day.

    Args:
        start_date (Union[datetime.datetime, str]): The first date in the set of partitions will
            Sunday at midnight following start_date. Can provide in either a datetime or string
            format.
        minute_offset (int): Number of minutes past the hour to "split" the partition. Defaults
            to 0.
        hour_offset (int): Number of hours past 00:00 to "split" the partition. Defaults to 0.
        day_offset (int): Day of the week to "split" the partition. Defaults to 0 (Sunday).
        timezone (Optional[str]): The timezone in which each date should exist.
            Supported strings for timezones are the ones provided by the
            `IANA time zone database <https://www.iana.org/time-zones>` - e.g. "America/Los_Angeles".
        fmt (Optional[str]): The date format to use. Defaults to `%Y-%m-%d`.
        end_offset (int): Extends the partition set by a number of partitions equal to the value
            passed. If end_offset is 0 (the default), the last partition ends before the current
            time. If end_offset is 1, the second-to-last partition ends before the current time,
            and so on.
        tags_for_partition_fn (Optional[Callable[[str], Mapping[str, str]]]): A function that
            accepts a partition time window and returns a dictionary of tags to attach to runs for
            that partition.

    .. code-block:: python

        @weekly_partitioned_config(start_date="2022-03-12")
        # creates partitions (2022-03-13-00:00, 2022-03-20-00:00), (2022-03-20-00:00, 2022-03-27-00:00), ...

        @weekly_partitioned_config(start_date="2022-03-12", minute_offset=15, hour_offset=3, day_offset=6)
        # creates partitions (2022-03-12-03:15, 2022-03-19-03:15), (2022-03-19-03:15, 2022-03-26-03:15), ...
    """

    def inner(
        fn: Callable[[datetime, datetime], Mapping[str, Any]],
    ) -> PartitionedConfig[WeeklyPartitionsDefinition]:
        check.callable_param(fn, "fn")

        partitions_def = WeeklyPartitionsDefinition(
            start_date=start_date,
            minute_offset=minute_offset,
            hour_offset=hour_offset,
            day_offset=day_offset,
            timezone=timezone,
            fmt=fmt,
            end_offset=end_offset,
        )
        return PartitionedConfig(
            run_config_for_partition_key_fn=wrap_time_window_run_config_fn(fn, partitions_def),
            partitions_def=partitions_def,
            decorated_fn=fn,
            tags_for_partition_key_fn=wrap_time_window_tags_fn(
                tags_for_partition_fn, partitions_def
            ),
        )

    return inner


class BaseTimeWindowPartitionsSubset(PartitionsSubset):
    """A base class that represents PartitionSubsets for TimeWindowPartitionsDefinitions.
    Contains shared logic for time window partitions subsets, such as building time windows
    from partition keys.
    """

    # Every time we change the serialization format, we should increment the version number.
    # This will ensure that we can gracefully degrade when deserializing old data.
    SERIALIZATION_VERSION = 1

    @abstractproperty
    def included_time_windows(self) -> Sequence[PersistedTimeWindow]: ...

    @abstractproperty
    def num_partitions(self) -> int: ...

    @abstractproperty
    def partitions_def(self) -> TimeWindowPartitionsDefinition: ...

    def _get_partition_time_windows_not_in_subset(
        self,
        current_time: Optional[datetime] = None,
    ) -> Sequence[PersistedTimeWindow]:
        """Returns a list of partition time windows that are not in the subset.
        Each time window is a single partition.
        """
        first_tw = cast(
            TimeWindowPartitionsDefinition, self.partitions_def
        ).get_first_partition_window(current_time=current_time)
        last_tw = cast(
            TimeWindowPartitionsDefinition, self.partitions_def
        ).get_last_partition_window(current_time=current_time)

        if not first_tw or not last_tw:
            # no partitions
            return []

        last_tw_end_timestamp = last_tw.end.timestamp()
        first_tw_start_timestamp = first_tw.start.timestamp()

        if len(self.included_time_windows) == 0:
            return [
                PersistedTimeWindow.from_public_time_window(
                    TimeWindow(first_tw.start, last_tw.end), self.partitions_def.timezone
                )
            ]

        time_windows = []
        if first_tw_start_timestamp < self.included_time_windows[0].start.timestamp():
            time_windows.append(
                PersistedTimeWindow.from_public_time_window(
                    TimeWindow(first_tw.start, self.included_time_windows[0].start),
                    self.partitions_def.timezone,
                )
            )

        for i in range(len(self.included_time_windows) - 1):
            if self.included_time_windows[i].start.timestamp() >= last_tw_end_timestamp:
                break
            if self.included_time_windows[i].end.timestamp() < last_tw_end_timestamp:
                if self.included_time_windows[i + 1].start.timestamp() <= last_tw_end_timestamp:
                    time_windows.append(
                        PersistedTimeWindow.from_public_time_window(
                            TimeWindow(
                                self.included_time_windows[i].end,
                                self.included_time_windows[i + 1].start,
                            ),
                            self.partitions_def.timezone,
                        )
                    )
                else:
                    time_windows.append(
                        PersistedTimeWindow.from_public_time_window(
                            TimeWindow(
                                self.included_time_windows[i].end,
                                last_tw.end,
                            ),
                            self.partitions_def.timezone,
                        )
                    )

        if last_tw_end_timestamp > self.included_time_windows[-1].end.timestamp():
            time_windows.append(
                PersistedTimeWindow.from_public_time_window(
                    TimeWindow(self.included_time_windows[-1].end, last_tw.end),
                    self.partitions_def.timezone,
                )
            )

        return time_windows

    def get_partition_keys_not_in_subset(
        self,
        partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> Iterable[str]:
        partition_keys: List[str] = []
        for tw in self._get_partition_time_windows_not_in_subset(current_time):
            partition_keys.extend(
                cast(
                    TimeWindowPartitionsDefinition, self.partitions_def
                ).get_partition_keys_in_time_window(tw)
            )
        return partition_keys

    @abstractproperty
    def first_start(self) -> datetime: ...

    @abstractproperty
    def is_empty(self) -> bool: ...

    @abstractmethod
    def cheap_ends_before(self, dt: datetime, dt_cron_schedule: str) -> bool: ...

    @abstractmethod
    def with_partitions_def(
        self, partitions_def: TimeWindowPartitionsDefinition
    ) -> "BaseTimeWindowPartitionsSubset": ...

    def get_partition_key_ranges(
        self,
        partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> Sequence[PartitionKeyRange]:
        return [
            cast(
                TimeWindowPartitionsDefinition, self.partitions_def
            ).get_partition_key_range_for_time_window(window.to_public_time_window())
            for window in self.included_time_windows
        ]

    def _add_partitions_to_time_windows(
        self,
        initial_windows: Sequence[PersistedTimeWindow],
        partition_keys: Sequence[str],
        validate: bool = True,
    ) -> Tuple[Sequence[PersistedTimeWindow], int]:
        """Merges a set of partition keys into an existing set of time windows, returning the
        minimized set of time windows and the number of partitions added.
        """
        result_windows = [*initial_windows]
        time_windows = cast(
            TimeWindowPartitionsDefinition, self.partitions_def
        ).time_windows_for_partition_keys(frozenset(partition_keys), validate=validate)

        num_added_partitions = 0
        for window in sorted(time_windows, key=lambda tw: tw.start.timestamp()):
            window_start_timestamp = window.start.timestamp()
            # go in reverse order because it's more common to add partitions at the end than the
            # beginning
            for i in reversed(range(len(result_windows))):
                included_window = result_windows[i]
                lt_end_of_range = window_start_timestamp < included_window.end.timestamp()
                gte_start_of_range = window_start_timestamp >= included_window.start.timestamp()

                if lt_end_of_range and gte_start_of_range:
                    break

                if not lt_end_of_range:
                    merge_with_range = included_window.end.timestamp() == window_start_timestamp
                    merge_with_later_range = i + 1 < len(result_windows) and (
                        window.end.timestamp() == result_windows[i + 1].start.timestamp()
                    )

                    if merge_with_range and merge_with_later_range:
                        result_windows[i] = PersistedTimeWindow.from_public_time_window(
                            TimeWindow(included_window.start, result_windows[i + 1].end),
                            self.partitions_def.timezone,
                        )
                        del result_windows[i + 1]
                    elif merge_with_range:
                        result_windows[i] = PersistedTimeWindow.from_public_time_window(
                            TimeWindow(included_window.start, window.end),
                            self.partitions_def.timezone,
                        )
                    elif merge_with_later_range:
                        result_windows[i + 1] = PersistedTimeWindow.from_public_time_window(
                            TimeWindow(window.start, result_windows[i + 1].end),
                            self.partitions_def.timezone,
                        )
                    else:
                        result_windows.insert(
                            i + 1,
                            PersistedTimeWindow.from_public_time_window(
                                window, self.partitions_def.timezone
                            ),
                        )

                    num_added_partitions += 1
                    break
            else:
                if result_windows and window_start_timestamp == result_windows[0].start.timestamp():
                    result_windows[0] = PersistedTimeWindow.from_public_time_window(
                        TimeWindow(window.start, included_window.end), self.partitions_def.timezone
                    )
                elif (
                    result_windows and window.end.timestamp() == result_windows[0].start.timestamp()
                ):
                    result_windows[0] = PersistedTimeWindow.from_public_time_window(
                        TimeWindow(window.start, included_window.end), self.partitions_def.timezone
                    )
                else:
                    result_windows.insert(
                        0,
                        PersistedTimeWindow.from_public_time_window(
                            window,
                            self.partitions_def.timezone,
                        ),
                    )

                num_added_partitions += 1

        return result_windows, num_added_partitions

    def serialize(self) -> str:
        return json.dumps(
            {
                "version": self.SERIALIZATION_VERSION,
                # included_time_windows is already sorted, so no need to sort here to guarantee
                # stable serialization between identical subsets
                "time_windows": [
                    (window.start.timestamp(), window.end.timestamp())
                    for window in self.included_time_windows
                ],
                "num_partitions": self.num_partitions,
            }
        )

    @classmethod
    def from_serialized(
        cls, partitions_def: PartitionsDefinition, serialized: str
    ) -> "PartitionsSubset":
        if not isinstance(partitions_def, TimeWindowPartitionsDefinition):
            check.failed("Partitions definition must be a TimeWindowPartitionsDefinition")
        partitions_def = cast(TimeWindowPartitionsDefinition, partitions_def)

        loaded = json.loads(serialized)

        def tuples_to_time_windows(tuples):
            return [
                PersistedTimeWindow(
                    TimestampWithTimezone(tup[0], partitions_def.timezone),
                    TimestampWithTimezone(tup[1], partitions_def.timezone),
                )
                for tup in tuples
            ]

        if isinstance(loaded, list):
            # backwards compatibility
            time_windows = tuples_to_time_windows(loaded)
            num_partitions = sum(
                len(partitions_def.get_partition_keys_in_time_window(time_window))
                for time_window in time_windows
            )
        elif isinstance(loaded, dict) and (
            "version" not in loaded or loaded["version"] == cls.SERIALIZATION_VERSION
        ):  # version 1
            time_windows = tuples_to_time_windows(loaded["time_windows"])
            num_partitions = loaded["num_partitions"]
        else:
            raise DagsterInvalidDeserializationVersionError(
                f"Attempted to deserialize partition subset with version {loaded.get('version')},"
                f" but only version {cls.SERIALIZATION_VERSION} is supported."
            )

        return TimeWindowPartitionsSubset(
            partitions_def, num_partitions=num_partitions, included_time_windows=time_windows
        )

    @classmethod
    def can_deserialize(
        cls,
        partitions_def: PartitionsDefinition,
        serialized: str,
        serialized_partitions_def_unique_id: Optional[str],
        serialized_partitions_def_class_name: Optional[str],
    ) -> bool:
        if serialized_partitions_def_unique_id:
            return (
                partitions_def.get_serializable_unique_identifier()
                == serialized_partitions_def_unique_id
            )

        if (
            serialized_partitions_def_class_name
            # note: all TimeWindowPartitionsDefinition subclasses will get serialized as raw
            # TimeWindowPartitionsDefinitions, so this class name check will not always pass,
            # hence the unique id check above
            and serialized_partitions_def_class_name != partitions_def.__class__.__name__
        ):
            return False

        data = json.loads(serialized)
        return isinstance(data, list) or (
            isinstance(data, dict)
            and data.get("time_windows") is not None
            and data.get("num_partitions") is not None
        )

    def __len__(self) -> int:
        return self.num_partitions

    def __contains__(self, partition_key: Optional[str]) -> bool:
        if partition_key is None:
            return False

        try:
            time_window = cast(
                TimeWindowPartitionsDefinition, self.partitions_def
            ).time_window_for_partition_key(partition_key)
        except ValueError:
            # invalid partition key
            return False

        time_window_start_timestamp = time_window.start.timestamp()

        return any(
            time_window_start_timestamp >= included_time_window.start.timestamp()
            and time_window_start_timestamp < included_time_window.end.timestamp()
            for included_time_window in self.included_time_windows
        )

    def __eq__(self, other):
        return (
            isinstance(other, BaseTimeWindowPartitionsSubset)
            and self.partitions_def == other.partitions_def
            and self.included_time_windows == other.included_time_windows
        )


class PartitionKeysTimeWindowPartitionsSubset(BaseTimeWindowPartitionsSubset):
    """A PartitionsSubset for a TimeWindowPartitionsDefinition, which internally represents the
    included partitions using strings.
    """

    def __init__(
        self,
        partitions_def: TimeWindowPartitionsDefinition,
        included_partition_keys: AbstractSet[str],
    ):
        self._partitions_def = check.inst_param(
            partitions_def, "partitions_def", TimeWindowPartitionsDefinition
        )
        self._included_partition_keys = check.set_param(
            included_partition_keys, "included_partition_keys", of_type=str
        )

    @property
    def partitions_def(self) -> TimeWindowPartitionsDefinition:
        return self._partitions_def

    def with_partition_keys(
        self, partition_keys: Iterable[str]
    ) -> "BaseTimeWindowPartitionsSubset":
        new_partitions = {*(self._included_partition_keys or []), *partition_keys}
        return PartitionKeysTimeWindowPartitionsSubset(
            self._partitions_def,
            included_partition_keys=new_partitions,
        )

    @cached_property
    def included_time_windows(self) -> Sequence[PersistedTimeWindow]:
        result_time_windows, _ = self._add_partitions_to_time_windows(
            initial_windows=[],
            partition_keys=list(check.not_none(self._included_partition_keys)),
            validate=False,
        )
        return result_time_windows

    @cached_property
    def num_partitions(self) -> int:
        return len(self._included_partition_keys)

    @public
    def get_partition_keys(self) -> Iterable[str]:
        return list(self._included_partition_keys) if self._included_partition_keys else []

    @property
    def first_start(self) -> datetime:
        """The start datetime of the earliest partition in the subset."""
        if len(self._included_partition_keys) == 1:
            # Avoid expensive conversion from partition keys to time windows if possible
            return self._partitions_def.start_time_for_partition_key(
                next(iter(self._included_partition_keys))
            )
        else:
            if len(self.included_time_windows) == 0:
                check.failed(
                    f"Empty subset. self._included_partition_keys: {self._included_partition_keys}"
                )
            return self.included_time_windows[0].start

    @property
    def is_empty(self) -> bool:
        return len(self._included_partition_keys) == 0

    def cheap_ends_before(self, dt: datetime, dt_cron_schedule: str) -> bool:
        """Performs a cheap calculation that checks whether the latest window in this subset ends
        before the given dt. If this returns True, then it means the latest window definitely ends
        before the given dt. If this returns False, it means it may or may not end before the given
        dt.

        Args:
            dt_cron_schedule (str): A cron schedule that dt is on one of the ticks of.
        """
        if len(self._included_partition_keys) == 1:
            # Getting just the partition start time is cheaper than invoking croniter to get the
            # full window.
            # If we know that the start time is earlier than dt and that the partitions are slim
            # enough that the end time can't put them past dt, then we know that the end time is
            # earlier than dt.
            if (self._partitions_def.cron_schedule == dt_cron_schedule) or (
                self._partitions_def.is_basic_hourly
                and dt_cron_schedule in ["0 0 * * *", "0 * * * *"]
            ):
                return (
                    self._partitions_def.start_time_for_partition_key(
                        next(iter(self._included_partition_keys))
                    )
                    < dt
                )

        return False

    def __contains__(self, partition_key: str) -> bool:
        return partition_key in self._included_partition_keys

    def __eq__(self, other):
        return (
            isinstance(other, PartitionKeysTimeWindowPartitionsSubset)
            and self._partitions_def == other._partitions_def
            and self._included_partition_keys == other._included_partition_keys
        ) or super(PartitionKeysTimeWindowPartitionsSubset, self).__eq__(other)

    @classmethod
    def empty_subset(
        cls, partitions_def: Optional[PartitionsDefinition] = None
    ) -> "PartitionsSubset":
        if not isinstance(partitions_def, TimeWindowPartitionsDefinition):
            check.failed("Partitions definition must be a TimeWindowPartitionsDefinition")
        partitions_def = cast(TimeWindowPartitionsDefinition, partitions_def)
        return cls(partitions_def, set())

    def with_partitions_def(
        self, partitions_def: TimeWindowPartitionsDefinition
    ) -> "BaseTimeWindowPartitionsSubset":
        check.invariant(
            partitions_def.cron_schedule == self._partitions_def.cron_schedule,
            "num_partitions would become inaccurate if the partitions_defs had different cron"
            " schedules",
        )
        return PartitionKeysTimeWindowPartitionsSubset(
            partitions_def=partitions_def,
            included_partition_keys=self._included_partition_keys,
        )

    def __repr__(self) -> str:
        return f"PartitionKeysTimeWindowPartitionsSubset({self.get_partition_key_ranges(self.partitions_def)})"

    def to_serializable_subset(self) -> "TimeWindowPartitionsSubset":
        from dagster._core.remote_representation.external_data import TimeWindowPartitionsSnap

        # in cases where we're dealing with (e.g.) HourlyPartitionsDefinition, we need to convert
        # this partitions definition into a raw TimeWindowPartitionsDefinition to make it
        # serializable. to do this, we just convert it to its external representation and back.
        partitions_def = self.partitions_def
        if type(self.partitions_def) != TimeWindowPartitionsSubset:
            partitions_def = TimeWindowPartitionsSnap.from_def(
                partitions_def
            ).get_partitions_definition()
        return TimeWindowPartitionsSubset(
            partitions_def, self.num_partitions, self.included_time_windows
        )

    def __or__(self, other: "PartitionsSubset") -> "PartitionsSubset":
        if isinstance(other, PartitionKeysTimeWindowPartitionsSubset):
            return self.partitions_def.subset_with_partition_keys(
                set(self.get_partition_keys()) | set(other.get_partition_keys())
            )
        return _attempt_coerce_to_time_window_subset(self) | _attempt_coerce_to_time_window_subset(
            other
        )

    def __sub__(self, other: "PartitionsSubset") -> "PartitionsSubset":
        if isinstance(other, PartitionKeysTimeWindowPartitionsSubset):
            return self.partitions_def.subset_with_partition_keys(
                set(self.get_partition_keys()) - set(other.get_partition_keys())
            )
        return _attempt_coerce_to_time_window_subset(self) - _attempt_coerce_to_time_window_subset(
            other
        )

    def __and__(self, other: "PartitionsSubset") -> "PartitionsSubset":
        if isinstance(other, PartitionKeysTimeWindowPartitionsSubset):
            return self.partitions_def.subset_with_partition_keys(
                set(self.get_partition_keys()) & set(other.get_partition_keys())
            )
        return _attempt_coerce_to_time_window_subset(self) & _attempt_coerce_to_time_window_subset(
            other
        )


class TimeWindowPartitionsSubsetSerializer(NamedTupleSerializer):
    # TimeWindowPartitionsSubsets have custom logic to delay calculating num_partitions until it
    # is needed to improve performance. When serializing, we want to serialize the number of
    # partitions, so we force calculation.
    def before_pack(self, value: "TimeWindowPartitionsSubset") -> "TimeWindowPartitionsSubset":
        # value.num_partitions will calculate the number of partitions if the field is None
        # We want to check if the field is None and replace the value with the calculated value
        # for serialization
        if value._asdict()["num_partitions"] is None:
            return TimeWindowPartitionsSubset(
                partitions_def=value.partitions_def,
                num_partitions=value.num_partitions,
                included_time_windows=value.included_time_windows,
            )
        return value


@whitelist_for_serdes(serializer=TimeWindowPartitionsSubsetSerializer)
class TimeWindowPartitionsSubset(
    BaseTimeWindowPartitionsSubset,
    NamedTuple(
        "_TimeWindowPartitionsSubset",
        [
            ("partitions_def", TimeWindowPartitionsDefinition),
            ("num_partitions", Optional[int]),
            ("included_time_windows", Sequence[PersistedTimeWindow]),
        ],
    ),
):
    """A PartitionsSubset for a TimeWindowPartitionsDefinition, which internally represents the
    included partitions using TimeWindows.
    """

    def __new__(
        cls,
        partitions_def: TimeWindowPartitionsDefinition,
        num_partitions: Optional[int],
        included_time_windows: Sequence[Union[PersistedTimeWindow, TimeWindow]],
    ):
        included_time_windows = [
            PersistedTimeWindow.from_public_time_window(tw, partitions_def.timezone)
            if isinstance(tw, TimeWindow)
            else tw
            for tw in included_time_windows
        ]

        return super(TimeWindowPartitionsSubset, cls).__new__(
            cls,
            partitions_def=check.inst_param(
                partitions_def, "partitions_def", TimeWindowPartitionsDefinition
            ),
            num_partitions=check.opt_int_param(num_partitions, "num_partitions"),
            included_time_windows=check.sequence_param(
                included_time_windows, "included_time_windows", of_type=PersistedTimeWindow
            ),
        )

    @staticmethod
    def from_all_partitions_subset(subset: AllPartitionsSubset) -> "TimeWindowPartitionsSubset":
        partitions_def = check.inst(
            subset.partitions_def,
            TimeWindowPartitionsDefinition,
            "Provided subset must reference a TimeWindowPartitionsDefinition",
        )
        first_window = partitions_def.get_first_partition_window(subset.current_time)
        last_window = partitions_def.get_last_partition_window(subset.current_time)
        return TimeWindowPartitionsSubset(
            partitions_def=partitions_def,
            included_time_windows=[
                PersistedTimeWindow.from_public_time_window(
                    TimeWindow(first_window.start, last_window.end), partitions_def.timezone
                )
            ]
            if first_window and last_window
            else [],
            num_partitions=None,
        )

    @cached_property
    def included_time_windows(self) -> Sequence[PersistedTimeWindow]:
        return self._asdict()["included_time_windows"]

    @property
    def partitions_def(self) -> TimeWindowPartitionsDefinition:
        return self._asdict()["partitions_def"]

    @property
    def first_start(self) -> datetime:
        """The start datetime of the earliest partition in the subset."""
        if len(self.included_time_windows) == 0:
            check.failed("Empty subset")
        return self.included_time_windows[0].start

    @property
    def is_empty(self) -> bool:
        return len(self.included_time_windows) == 0

    def cheap_ends_before(self, dt: datetime, dt_cron_schedule: str) -> bool:
        """Performs a cheap calculation that checks whether the latest window in this subset ends
        before the given dt. If this returns True, then it means the latest window definitely ends
        before the given dt. If this returns False, it means it may or may not end before the given
        dt.

        Args:
            dt_cron_schedule (str): A cron schedule that dt is on one of the ticks of.
        """
        return self.included_time_windows[-1].end.timestamp() <= dt.timestamp()

    @cached_property
    def num_partitions(self) -> int:
        num_partitions_ = self._asdict()["num_partitions"]
        if num_partitions_ is None:
            return sum(
                self.partitions_def.get_num_partitions_in_window(
                    time_window.to_public_time_window()
                )
                for time_window in self.included_time_windows
            )
        return num_partitions_

    @classmethod
    def _num_partitions_from_time_windows(
        cls,
        partitions_def: TimeWindowPartitionsDefinition,
        time_windows: Sequence[PersistedTimeWindow],
    ) -> int:
        return sum(
            len(partitions_def.get_partition_keys_in_time_window(time_window))
            for time_window in time_windows
        )

    @public
    def get_partition_keys(self) -> Iterable[str]:
        return [
            pk
            for time_window in self.included_time_windows
            for pk in self.partitions_def.get_partition_keys_in_time_window(time_window)
        ]

    def with_partition_keys(self, partition_keys: Iterable[str]) -> "TimeWindowPartitionsSubset":
        result_windows, added_partitions = self._add_partitions_to_time_windows(
            self.included_time_windows, list(partition_keys)
        )

        return TimeWindowPartitionsSubset(
            self.partitions_def,
            num_partitions=self.num_partitions + added_partitions,
            included_time_windows=result_windows,
        )

    @classmethod
    def empty_subset(
        cls, partitions_def: Optional[PartitionsDefinition] = None
    ) -> "PartitionsSubset":
        if not isinstance(partitions_def, TimeWindowPartitionsDefinition):
            check.failed("Partitions definition must be a TimeWindowPartitionsDefinition")
        partitions_def = cast(TimeWindowPartitionsDefinition, partitions_def)
        return cls(partitions_def, 0, [])

    def with_partitions_def(
        self, partitions_def: TimeWindowPartitionsDefinition
    ) -> "TimeWindowPartitionsSubset":
        check.invariant(
            partitions_def.cron_schedule == self.partitions_def.cron_schedule,
            "num_partitions would become inaccurate if the partitions_defs had different cron"
            " schedules",
        )
        return TimeWindowPartitionsSubset(
            partitions_def=partitions_def,
            num_partitions=self.num_partitions,
            included_time_windows=self.included_time_windows,
        )

    def __repr__(self) -> str:
        return f"TimeWindowPartitionsSubset({self.get_partition_key_ranges(self.partitions_def)})"

    def __and__(self, other: "PartitionsSubset") -> "PartitionsSubset":
        other = _attempt_coerce_to_time_window_subset(other)
        if not isinstance(other, TimeWindowPartitionsSubset):
            return super().__and__(other)

        self_time_windows_iter = iter(
            sorted(self.included_time_windows, key=lambda tw: tw.start.timestamp())
        )
        other_time_windows_iter = iter(
            sorted(other.included_time_windows, key=lambda tw: tw.start.timestamp())
        )

        result_windows = []
        self_window = next(self_time_windows_iter, None)
        other_window = next(other_time_windows_iter, None)
        while self_window and other_window:
            # find the intersection between the current two windows
            start = max(self_window.start, other_window.start)
            end = min(self_window.end, other_window.end)

            # these windows intersect
            if start.timestamp() < end.timestamp():
                result_windows.append(
                    PersistedTimeWindow.from_public_time_window(
                        TimeWindow(start=start, end=end), self.partitions_def.timezone
                    )
                )

            # advance the iterator with the earliest end time to find the next potential intersection
            if self_window.end.timestamp() < other_window.end.timestamp():
                self_window = next(self_time_windows_iter, None)
            else:
                other_window = next(other_time_windows_iter, None)

        return TimeWindowPartitionsSubset(
            partitions_def=self.partitions_def,
            num_partitions=None,  # lazily calculated
            included_time_windows=result_windows,
        )

    def __or__(self, other: "PartitionsSubset") -> "PartitionsSubset":
        other = _attempt_coerce_to_time_window_subset(other)
        if not isinstance(other, TimeWindowPartitionsSubset):
            return super().__or__(other)

        input_time_windows = sorted(
            [*self.included_time_windows, *other.included_time_windows],
            key=lambda tw: tw.start.timestamp(),
        )
        result_windows = [input_time_windows[0]] if len(input_time_windows) > 0 else []
        for window in input_time_windows[1:]:
            latest_window = result_windows[-1]
            if window.start.timestamp() <= latest_window.end.timestamp():
                # merge this window with the latest window
                result_windows[-1] = PersistedTimeWindow.from_public_time_window(
                    TimeWindow(latest_window.start, max(latest_window.end, window.end)),
                    self.partitions_def.timezone,
                )
            else:
                result_windows.append(window)

        return TimeWindowPartitionsSubset(
            partitions_def=self.partitions_def,
            num_partitions=None,  # lazily calculated
            included_time_windows=result_windows,
        )

    def __sub__(self, other: "PartitionsSubset") -> "PartitionsSubset":
        other = _attempt_coerce_to_time_window_subset(other)
        if not isinstance(other, TimeWindowPartitionsSubset):
            return super().__sub__(other)

        time_windows = sorted(self.included_time_windows, key=lambda tw: tw.start.timestamp())
        other_time_windows = sorted(
            other.included_time_windows, key=lambda tw: tw.start.timestamp()
        )

        next_time_window_index_to_process = 0
        next_other_window_index_to_process = 0

        # Slide through both sets of windows, moving to the next window once its start has passed
        # the end of the window is it being compared to
        while (next_time_window_index_to_process < len(time_windows)) and (
            next_other_window_index_to_process < len(other_time_windows)
        ):
            time_window = time_windows[next_time_window_index_to_process]
            other_time_window = other_time_windows[next_other_window_index_to_process]

            # Perform the subtraction and splice the 0, 1, or 2 result windows
            # back into the time_windows list

            subtracted_time_windows = time_window.subtract(other_time_window)

            time_windows[
                next_time_window_index_to_process : next_time_window_index_to_process + 1
            ] = subtracted_time_windows

            if len(subtracted_time_windows) == 0:
                # other_time_window fully consumed time_window
                # next_time_window_index_to_process can stay the same since everything has shifted over one
                pass
            else:
                updated_time_window = time_windows[next_time_window_index_to_process]
                if updated_time_window.end.timestamp() <= other_time_window.start.timestamp():
                    # Current subtractor is too early to intersect, can advance
                    next_time_window_index_to_process += 1
                elif other_time_window.end.timestamp() <= updated_time_window.start.timestamp():
                    # current subtractee is too early to intersect, can advance
                    next_other_window_index_to_process += 1
                else:
                    check.failed(
                        "After subtraction, the new window should no longer intersect with the other window"
                    )

        return TimeWindowPartitionsSubset(
            partitions_def=self.partitions_def,
            num_partitions=None,
            included_time_windows=time_windows,
        )

    def to_serializable_subset(self) -> "TimeWindowPartitionsSubset":
        from dagster._core.remote_representation.external_data import TimeWindowPartitionsSnap

        # in cases where we're dealing with (e.g.) HourlyPartitionsDefinition, we need to convert
        # this partitions definition into a raw TimeWindowPartitionsDefinition to make it
        # serializable. to do this, we just convert it to its external representation and back.
        # note that we rarely serialize subsets on the user code side of a serialization boundary,
        # and so this conversion is rarely necessary.
        partitions_def = self.partitions_def
        if type(self.partitions_def) != TimeWindowPartitionsSubset:
            partitions_def = TimeWindowPartitionsSnap.from_def(
                partitions_def
            ).get_partitions_definition()
            return self.with_partitions_def(partitions_def)
        return self


class PartitionRangeStatus(Enum):
    MATERIALIZING = "MATERIALIZING"
    MATERIALIZED = "MATERIALIZED"
    FAILED = "FAILED"


PARTITION_RANGE_STATUS_PRIORITY = [
    PartitionRangeStatus.MATERIALIZING,
    PartitionRangeStatus.FAILED,
    PartitionRangeStatus.MATERIALIZED,
]


class PartitionTimeWindowStatus:
    def __init__(self, time_window: TimeWindow, status: PartitionRangeStatus):
        self.time_window = time_window
        self.status = status

    def __repr__(self):
        return f"({self.time_window.start} - {self.time_window.end}): {self.status.value}"

    def __eq__(self, other):
        return (
            isinstance(other, PartitionTimeWindowStatus)
            and self.time_window == other.time_window
            and self.status == other.status
        )


def _flatten(
    high_pri_time_windows: List[PartitionTimeWindowStatus],
    low_pri_time_windows: List[PartitionTimeWindowStatus],
) -> List[PartitionTimeWindowStatus]:
    high_pri_time_windows = sorted(high_pri_time_windows, key=lambda t: t.time_window.start)
    low_pri_time_windows = sorted(low_pri_time_windows, key=lambda t: t.time_window.start)

    high_pri_idx = 0
    low_pri_idx = 0

    filtered_low_pri: List[PartitionTimeWindowStatus] = []

    # slice and dice the low pri time windows so there's no overlap with high pri
    while True:
        if low_pri_idx >= len(low_pri_time_windows):
            # reached end of materialized
            break
        if high_pri_idx >= len(high_pri_time_windows):
            # reached end of failed, add all remaining materialized bc there's no overlap
            filtered_low_pri.extend(low_pri_time_windows[low_pri_idx:])
            break

        low_pri_tw = low_pri_time_windows[low_pri_idx]
        high_pri_tw = high_pri_time_windows[high_pri_idx]

        if low_pri_tw.time_window.start.timestamp() < high_pri_tw.time_window.start.timestamp():
            if low_pri_tw.time_window.end.timestamp() <= high_pri_tw.time_window.start.timestamp():
                # low_pri_tw is entirely before high pri
                filtered_low_pri.append(low_pri_tw)
                low_pri_idx += 1
            else:
                # high pri cuts the low pri short
                filtered_low_pri.append(
                    PartitionTimeWindowStatus(
                        TimeWindow(
                            low_pri_tw.time_window.start,
                            high_pri_tw.time_window.start,
                        ),
                        low_pri_tw.status,
                    )
                )

                if low_pri_tw.time_window.end.timestamp() > high_pri_tw.time_window.end.timestamp():
                    # the low pri time window will continue on the other end of the high pri
                    # and get split in two. Modify low_pri[low_pri_idx] to be
                    # the second half of the low pri time window. It will be added in the next iteration.
                    # (don't add it now, because we need to check if it overlaps with the next high pri)
                    low_pri_time_windows[low_pri_idx] = PartitionTimeWindowStatus(
                        TimeWindow(high_pri_tw.time_window.end, low_pri_tw.time_window.end),
                        low_pri_tw.status,
                    )
                    high_pri_idx += 1
                else:
                    # the rest of the low pri time window is inside the high pri time window
                    low_pri_idx += 1
        else:
            if low_pri_tw.time_window.start.timestamp() >= high_pri_tw.time_window.end.timestamp():
                # high pri is entirely before low pri. The next high pri may overlap
                high_pri_idx += 1
            elif low_pri_tw.time_window.end.timestamp() <= high_pri_tw.time_window.end.timestamp():
                # low pri is entirely within high pri, skip it
                low_pri_idx += 1
            else:
                # high pri cuts out the start of the low pri. It will continue on the other end.
                # Modify low_pri[low_pri_idx] to shorten the start. It will be added
                # in the next iteration. (don't add it now, because we need to check if it overlaps with the next high pri)
                low_pri_time_windows[low_pri_idx] = PartitionTimeWindowStatus(
                    TimeWindow(high_pri_tw.time_window.end, low_pri_tw.time_window.end),
                    low_pri_tw.status,
                )
                high_pri_idx += 1

    # combine the high pri windwos with the filtered low pri windows
    flattened_time_windows = high_pri_time_windows
    flattened_time_windows.extend(filtered_low_pri)
    flattened_time_windows.sort(key=lambda t: t.time_window.start)
    return flattened_time_windows


def fetch_flattened_time_window_ranges(
    subsets: Mapping[PartitionRangeStatus, BaseTimeWindowPartitionsSubset],
) -> Sequence[PartitionTimeWindowStatus]:
    """Given potentially overlapping subsets, return a flattened list of timewindows where the highest priority status wins
    on overlaps.
    """
    prioritized_subsets = sorted(
        [(status, subset) for status, subset in subsets.items()],
        key=lambda t: PARTITION_RANGE_STATUS_PRIORITY.index(t[0]),
    )

    # progressively add lower priority time windows to the list of higher priority time windows
    flattened_time_window_statuses = []
    for status, subset in prioritized_subsets:
        subset_time_window_statuses = [
            PartitionTimeWindowStatus(tw.to_public_time_window(), status)
            for tw in subset.included_time_windows
        ]
        flattened_time_window_statuses = _flatten(
            flattened_time_window_statuses, subset_time_window_statuses
        )

    return flattened_time_window_statuses


def has_one_dimension_time_window_partitioning(
    partitions_def: Optional[PartitionsDefinition],
) -> bool:
    from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionsDefinition

    if isinstance(partitions_def, TimeWindowPartitionsDefinition):
        return True
    elif isinstance(partitions_def, MultiPartitionsDefinition):
        time_window_dims = [
            dim
            for dim in partitions_def.partitions_defs
            if isinstance(dim.partitions_def, TimeWindowPartitionsDefinition)
        ]
        if len(time_window_dims) == 1:
            return True

    return False


def get_time_partitions_def(
    partitions_def: Optional[PartitionsDefinition],
) -> Optional[TimeWindowPartitionsDefinition]:
    """For a given PartitionsDefinition, return the associated TimeWindowPartitionsDefinition if it
    exists.
    """
    from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionsDefinition

    if partitions_def is None:
        return None
    elif isinstance(partitions_def, TimeWindowPartitionsDefinition):
        return partitions_def
    elif isinstance(
        partitions_def, MultiPartitionsDefinition
    ) and has_one_dimension_time_window_partitioning(partitions_def):
        return cast(
            TimeWindowPartitionsDefinition, partitions_def.time_window_dimension.partitions_def
        )
    else:
        return None


def get_time_partition_key(
    partitions_def: Optional[PartitionsDefinition], partition_key: Optional[str]
) -> str:
    from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionsDefinition

    if partitions_def is None or partition_key is None:
        check.failed(
            "Cannot get time partitions key from when partitions def is None or partition key is"
            " None"
        )
    elif isinstance(partitions_def, TimeWindowPartitionsDefinition):
        return partition_key
    elif isinstance(partitions_def, MultiPartitionsDefinition):
        return partitions_def.get_partition_key_from_str(partition_key).keys_by_dimension[
            partitions_def.time_window_dimension.name
        ]
    else:
        check.failed(f"Cannot get time partition from non-time partitions def {partitions_def}")


def _attempt_coerce_to_time_window_subset(subset: "PartitionsSubset") -> "PartitionsSubset":
    """Attempts to convert the input subset into a TimeWindowPartitionsSubset."""
    if isinstance(subset, TimeWindowPartitionsSubset):
        return subset
    elif isinstance(subset, BaseTimeWindowPartitionsSubset):
        return TimeWindowPartitionsSubset(
            partitions_def=subset.partitions_def,
            num_partitions=subset.num_partitions,
            included_time_windows=subset.included_time_windows,
        )
    elif isinstance(subset, AllPartitionsSubset):
        return TimeWindowPartitionsSubset.from_all_partitions_subset(subset)
    else:
        return subset
