import hashlib
import json
import re
from datetime import datetime
from typing import (
    Any,
    Callable,
    Iterable,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Union,
    cast,
)

import pendulum

import dagster._check as check
from dagster._annotations import PublicAttr, public
from dagster._utils.partitions import DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE
from dagster._utils.schedules import cron_string_iterator, reverse_cron_string_iterator

from ..errors import DagsterInvalidDeserializationVersionError
from .partition import (
    DEFAULT_DATE_FORMAT,
    Partition,
    PartitionedConfig,
    PartitionsDefinition,
    PartitionsSubset,
    ScheduleType,
    cron_schedule_from_schedule_type_and_offsets,
)
from .partition_key_range import PartitionKeyRange


class TimeWindow(NamedTuple):
    """An interval that is closed at the start and open at the end.

    Attributes:
        start (datetime): A pendulum datetime that marks the start of the window.
        end (datetime): A pendulum datetime that marks the end of the window.
    """

    start: PublicAttr[datetime]
    end: PublicAttr[datetime]


class TimeWindowPartitionsDefinition(
    PartitionsDefinition[TimeWindow],  # pylint: disable=unsubscriptable-object
    NamedTuple(
        "_TimeWindowPartitionsDefinition",
        [
            ("start", PublicAttr[datetime]),
            ("timezone", PublicAttr[str]),
            ("fmt", PublicAttr[str]),
            ("end_offset", PublicAttr[int]),
            ("cron_schedule", PublicAttr[str]),
        ],
    ),
):
    r"""
    A set of partitions where each partitions corresponds to a time window.

    The provided cron_schedule determines the bounds of the time windows. E.g. a cron_schedule of
    "0 0 \\* \\* \\*" will result in daily partitions that start at midnight and end at midnight of the
    following day.

    The string partition_key associated with each partition corresponds to the start of the
    partition's time window.

    The first partition in the set will start on at the first cron_schedule tick that is equal to
    or after the given start datetime. The last partition in the set will end before the current
    time, unless the end_offset argument is set to a positive number.

    Args:
        cron_schedule (str): Determines the bounds of the time windows.
        start (datetime): The first partition in the set will start on at the first cron_schedule
            tick that is equal to or after this value.
        timezone (Optional[str]): The timezone in which each time should exist.
            Supported strings for timezones are the ones provided by the
            `IANA time zone database <https://www.iana.org/time-zones>` - e.g. "America/Los_Angeles".
        fmt (str): The date format to use for partition_keys.
        end_offset (int): Extends the partition set by a number of partitions equal to the value
            passed. If end_offset is 0 (the default), the last partition ends before the current
            time. If end_offset is 1, the second-to-last partition ends before the current time,
            and so on.
    """

    def __new__(  # pylint: disable=arguments-differ
        cls,
        start: Union[datetime, str],
        fmt: str,
        schedule_type: Optional[ScheduleType] = None,
        timezone: Optional[str] = None,
        end_offset: int = 0,
        minute_offset: Optional[int] = None,
        hour_offset: Optional[int] = None,
        day_offset: Optional[int] = None,
        cron_schedule: Optional[str] = None,
    ):
        if isinstance(start, datetime):
            start_dt = start
        else:
            start_dt = datetime.strptime(start, fmt)

        if cron_schedule is not None:
            check.invariant(
                schedule_type is None and not minute_offset and not hour_offset and not day_offset,
                (
                    "If cron_schedule argument is provided, then schedule_type, minute_offset, "
                    "hour_offset, and day_offset can't also be provided"
                ),
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

        return super(TimeWindowPartitionsDefinition, cls).__new__(
            cls, start_dt, timezone or "UTC", fmt, end_offset, cron_schedule
        )

    def get_partitions(
        self, current_time: Optional[datetime] = None
    ) -> Sequence[Partition[TimeWindow]]:
        current_timestamp = (
            pendulum.instance(current_time, tz=self.timezone)
            if current_time
            else pendulum.now(self.timezone)
        ).timestamp()

        partitions_past_current_time = 0
        partitions: List[Partition[TimeWindow]] = []
        for time_window in self._iterate_time_windows(self.start):
            if (
                time_window.end.timestamp() <= current_timestamp
                or partitions_past_current_time < self.end_offset
            ):
                partitions.append(
                    Partition(value=time_window, name=time_window.start.strftime(self.fmt))
                )

                if time_window.end.timestamp() > current_timestamp:
                    partitions_past_current_time += 1
            else:
                break

        if self.end_offset < 0:
            partitions = partitions[: self.end_offset]

        return partitions

    def __str__(self) -> str:
        schedule_str = (
            self.schedule_type.value.capitalize() if self.schedule_type else self.cron_schedule
        )
        partition_def_str = (
            f"{schedule_str}, starting {self.start.strftime(self.fmt)} {self.timezone}."
        )
        if self.end_offset != 0:
            partition_def_str += (
                " End offsetted by"
                f" {self.end_offset} partition{'' if self.end_offset == 1 else 's'}."
            )
        return partition_def_str

    def __eq__(self, other):
        return (
            isinstance(other, TimeWindowPartitionsDefinition)
            and pendulum.instance(self.start, tz=self.timezone).timestamp()
            == pendulum.instance(other.start, tz=other.timezone).timestamp()
            and self.timezone == other.timezone
            and self.fmt == other.fmt
            and self.end_offset == other.end_offset
            and self.cron_schedule == other.cron_schedule
        )

    def __hash__(self):
        return hash(tuple(self.__repr__()))

    def time_window_for_partition_key(self, partition_key: str) -> TimeWindow:
        partition_key_dt = pendulum.instance(
            datetime.strptime(partition_key, self.fmt), tz=self.timezone
        )
        return next(iter(self._iterate_time_windows(partition_key_dt)))

    def time_windows_for_partition_keys(
        self,
        partition_keys: Sequence[str],
    ) -> Sequence[TimeWindow]:
        if len(partition_keys) == 0:
            return []

        sorted_pks = sorted(partition_keys, key=lambda pk: datetime.strptime(pk, self.fmt))
        cur_windows_iterator = iter(
            self._iterate_time_windows(datetime.strptime(sorted_pks[0], self.fmt))
        )
        partition_key_time_windows: List[TimeWindow] = []
        for partition_key in sorted_pks:
            next_window = next(cur_windows_iterator)
            if next_window.start.strftime(self.fmt) == partition_key:
                partition_key_time_windows.append(next_window)
            else:
                cur_windows_iterator = iter(
                    self._iterate_time_windows(datetime.strptime(partition_key, self.fmt))
                )
                partition_key_time_windows.append(next(cur_windows_iterator))

        end_tw = self.get_last_partition_window()
        if end_tw is None:
            check.failed("No end time window found")
        end_timestamp = end_tw.end.timestamp()
        partition_key_time_windows = [
            tw
            for tw in partition_key_time_windows
            if tw.start.timestamp() >= self.start.timestamp()
            and tw.end.timestamp() <= end_timestamp
        ]
        return partition_key_time_windows

    def start_time_for_partition_key(self, partition_key: str) -> datetime:
        partition_key_dt = pendulum.instance(
            datetime.strptime(partition_key, self.fmt), tz=self.timezone
        )
        # the datetime format might not include granular components, so we need to recover them
        # we make the assumption that the parsed partition key is <= the start datetime
        return next(iter(self._iterate_time_windows(partition_key_dt))).start

    def get_next_partition_key(
        self, partition_key: str, current_time: Optional[datetime] = None
    ) -> Optional[str]:
        last_partition_window = self.get_last_partition_window(current_time)
        if last_partition_window is None:
            return None

        partition_key_dt = pendulum.instance(
            datetime.strptime(partition_key, self.fmt), tz=self.timezone
        )
        windows_iter = iter(self._iterate_time_windows(partition_key_dt))
        next(windows_iter)
        start_time = next(windows_iter).start
        if start_time >= last_partition_window.end:
            return None
        else:
            return start_time.strftime(self.fmt)

    def get_next_partition_window(
        self, end_dt: datetime, current_time: Optional[datetime] = None
    ) -> Optional[TimeWindow]:
        last_partition_window = self.get_last_partition_window(current_time)
        if last_partition_window is None:
            return None

        windows_iter = iter(self._iterate_time_windows(end_dt))
        next_window = next(windows_iter)
        if next_window.start >= last_partition_window.end:
            return None
        else:
            return next_window

    def get_prev_partition_window(self, start_dt: datetime) -> Optional[TimeWindow]:
        windows_iter = iter(self._reverse_iterate_time_windows(start_dt))
        prev_window = next(windows_iter)
        first_partition_window = self.get_first_partition_window()
        if first_partition_window is None or prev_window.start < first_partition_window.start:
            return None
        else:
            return prev_window

    def get_first_partition_window(
        self, current_time: Optional[datetime] = None
    ) -> Optional[TimeWindow]:
        current_timestamp = (
            pendulum.instance(current_time, tz=self.timezone)
            if current_time
            else pendulum.now(self.timezone)
        ).timestamp()

        time_window = next(iter(self._iterate_time_windows(self.start)))
        if time_window.end.timestamp() <= current_timestamp:
            return time_window
        else:
            return None

    def get_last_partition_window(
        self, current_time: Optional[datetime] = None
    ) -> Optional[TimeWindow]:
        if self.get_first_partition_window(current_time) is None:
            return None

        current_time = (
            pendulum.instance(current_time, tz=self.timezone)
            if current_time
            else pendulum.now(self.timezone)
        )

        if self.end_offset == 0:
            return next(iter(self._reverse_iterate_time_windows(current_time)))
        else:
            # TODO: make this efficient
            last_partition_key = super().get_last_partition_key(current_time)
            return (
                self.time_window_for_partition_key(last_partition_key)
                if last_partition_key
                else None
            )

    def get_last_partition_key(self, current_time: Optional[datetime] = None) -> Optional[str]:
        last_window = self.get_last_partition_window(current_time)
        if last_window is None:
            return None

        return last_window.start.strftime(self.fmt)

    def end_time_for_partition_key(self, partition_key: str) -> datetime:
        return self.time_window_for_partition_key(partition_key).end

    def get_default_partition_mapping(self):
        from dagster._core.definitions.time_window_partition_mapping import (
            TimeWindowPartitionMapping,
        )

        return TimeWindowPartitionMapping()

    def get_partition_keys_in_time_window(self, time_window: TimeWindow) -> Sequence[str]:
        result: List[str] = []
        for partition_time_window in self._iterate_time_windows(time_window.start):
            if partition_time_window.start < time_window.end:
                result.append(partition_time_window.start.strftime(self.fmt))
            else:
                break
        return result

    def get_partition_key_range_for_time_window(self, time_window: TimeWindow) -> PartitionKeyRange:
        start_partition_key = self.get_partition_key_for_timestamp(time_window.start.timestamp())
        end_partition_key = self.get_partition_key_for_timestamp(
            cast(TimeWindow, self.get_prev_partition_window(time_window.end)).start.timestamp()
        )

        return PartitionKeyRange(start_partition_key, end_partition_key)

    def get_partition_keys_in_range(self, partition_key_range: PartitionKeyRange) -> Sequence[str]:
        start_time = self.start_time_for_partition_key(partition_key_range.start)
        end_time = self.end_time_for_partition_key(partition_key_range.end)

        return self.get_partition_keys_in_time_window(TimeWindow(start_time, end_time))

    @public  # type: ignore
    @property
    def schedule_type(self) -> Optional[ScheduleType]:
        if re.match(r"\d+ \* \* \* \*", self.cron_schedule):
            return ScheduleType.HOURLY
        elif re.match(r"\d+ \d+ \* \* \*", self.cron_schedule):
            return ScheduleType.DAILY
        elif re.match(r"\d+ \d+ \* \* \d+", self.cron_schedule):
            return ScheduleType.WEEKLY
        elif re.match(r"\d+ \d+ \d+ \* \*", self.cron_schedule):
            return ScheduleType.MONTHLY
        else:
            return None

    @public  # type: ignore
    @property
    def minute_offset(self) -> int:
        match = re.match(r"(\d+) (\d+|\*) (\d+|\*) (\d+|\*) (\d+|\*)", self.cron_schedule)
        if match is None:
            check.failed(f"{self.cron_schedule} has no minute offset")
        return int(match.groups()[0])

    @public  # type: ignore
    @property
    def hour_offset(self) -> int:
        match = re.match(r"(\d+|\*) (\d+) (\d+|\*) (\d+|\*) (\d+|\*)", self.cron_schedule)
        if match is None:
            check.failed(f"{self.cron_schedule} has no hour offset")
        return int(match.groups()[1])

    @public  # type: ignore
    @property
    def day_offset(self) -> int:
        schedule_type = self.schedule_type
        if schedule_type == ScheduleType.WEEKLY:
            match = re.match(r"(\d+|\*) (\d+|\*) (\d+|\*) (\d+|\*) (\d+)", self.cron_schedule)
            if match is None:
                check.failed(f"{self.cron_schedule} has no day offset")
            return int(match.groups()[4])
        elif schedule_type == ScheduleType.MONTHLY:
            match = re.match(r"(\d+|\*) (\d+|\*) (\d+) (\d+|\*) (\d+|\*)", self.cron_schedule)
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

    def _iterate_time_windows(self, start: datetime) -> Iterable[TimeWindow]:
        """
        Returns an infinite generator of time windows that start after the given start time.
        """
        start_timestamp = pendulum.instance(start, tz=self.timezone).timestamp()
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

    def _reverse_iterate_time_windows(self, end: datetime) -> Iterable[TimeWindow]:
        """
        Returns an infinite generator of time windows that end before the given end time.
        """
        end_timestamp = pendulum.instance(end, tz=self.timezone).timestamp()
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
        """
        Args:
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
            return prev.strftime(self.fmt)
        else:
            return prev_next.strftime(self.fmt)

    def less_than(self, partition_key1: str, partition_key2: str) -> bool:
        """Returns true if the partition_key1 is earlier than partition_key2."""
        return self.start_time_for_partition_key(
            partition_key1
        ) < self.start_time_for_partition_key(partition_key2)

    def empty_subset(self) -> "TimeWindowPartitionsSubset":
        return TimeWindowPartitionsSubset(self, [], 0)

    def deserialize_subset(self, serialized: str) -> "PartitionsSubset":
        return TimeWindowPartitionsSubset.from_serialized(self, serialized)

    @property
    def serializable_unique_identifier(self) -> str:
        return hashlib.sha1(self.__repr__().encode("utf-8")).hexdigest()


class DailyPartitionsDefinition(TimeWindowPartitionsDefinition):
    def __new__(  # pylint: disable=signature-differs
        cls,
        start_date: Union[datetime, str],
        minute_offset: int = 0,
        hour_offset: int = 0,
        timezone: Optional[str] = None,
        fmt: Optional[str] = None,
        end_offset: int = 0,
    ):
        """A set of daily partitions.

        The first partition in the set will start at the start_date at midnight. The last partition
        in the set will end before the current time, unless the end_offset argument is set to a
        positive number. If minute_offset and/or hour_offset are used, the start and end times of
        each partition will be hour_offset:minute_offset of each day.

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

        .. code-block:: python
            DailyPartitionsDefinition(start_date="2022-03-12")
            # creates partitions (2022-03-12-00:00, 2022-03-13-00:00), (2022-03-13-00:00, 2022-03-14-00:00), ...

            DailyPartitionsDefinition(start_date="2022-03-12", minute_offset=15, hour_offset=16)
            # creates partitions (2022-03-12-16:15, 2022-03-13-16:15), (2022-03-13-16:15, 2022-03-14-16:15), ...
        """
        _fmt = fmt or DEFAULT_DATE_FORMAT

        return super(DailyPartitionsDefinition, cls).__new__(
            cls,
            schedule_type=ScheduleType.DAILY,
            start=start_date,
            minute_offset=minute_offset,
            hour_offset=hour_offset,
            timezone=timezone,
            fmt=_fmt,
            end_offset=end_offset,
        )


def wrap_time_window_tags_fn(
    tags_fn: Optional[Callable[[datetime, datetime], Mapping[str, str]]]
) -> Callable[[Partition], Mapping[str, str]]:
    def _tag_wrapper(partition: Partition) -> Mapping[str, str]:
        if not tags_fn:
            return {}
        return tags_fn(cast(datetime, partition.value[0]), cast(datetime, partition.value[1]))

    return _tag_wrapper


def daily_partitioned_config(
    start_date: Union[datetime, str],
    minute_offset: int = 0,
    hour_offset: int = 0,
    timezone: Optional[str] = None,
    fmt: Optional[str] = None,
    end_offset: int = 0,
    tags_for_partition_fn: Optional[Callable[[datetime, datetime], Mapping[str, str]]] = None,
) -> Callable[[Callable[[datetime, datetime], Mapping[str, Any]]], PartitionedConfig]:
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

    .. code-block:: python

        @daily_partitioned_config(start_date="2022-03-12")
        # creates partitions (2022-03-12-00:00, 2022-03-13-00:00), (2022-03-13-00:00, 2022-03-14-00:00), ...

        @daily_partitioned_config(start_date="2022-03-12", minute_offset=15, hour_offset=16)
        # creates partitions (2022-03-12-16:15, 2022-03-13-16:15), (2022-03-13-16:15, 2022-03-14-16:15), ...
    """

    def inner(fn: Callable[[datetime, datetime], Mapping[str, Any]]) -> PartitionedConfig:
        check.callable_param(fn, "fn")

        return PartitionedConfig(
            run_config_for_partition_fn=lambda partition: fn(
                partition.value[0], partition.value[1]
            ),
            partitions_def=DailyPartitionsDefinition(
                start_date=start_date,
                minute_offset=minute_offset,
                hour_offset=hour_offset,
                timezone=timezone,
                fmt=fmt,
                end_offset=end_offset,
            ),
            decorated_fn=fn,
            tags_for_partition_fn=wrap_time_window_tags_fn(tags_for_partition_fn),
        )

    return inner


class HourlyPartitionsDefinition(TimeWindowPartitionsDefinition):
    def __new__(  # pylint: disable=signature-differs
        cls,
        start_date: Union[datetime, str],
        minute_offset: int = 0,
        timezone: Optional[str] = None,
        fmt: Optional[str] = None,
        end_offset: int = 0,
    ):
        """A set of hourly partitions.

        The first partition in the set will start on the start_date at midnight. The last partition
        in the set will end before the current time, unless the end_offset argument is set to a
        positive number. If minute_offset is provided, the start and end times of each partition
        will be minute_offset past the hour.

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

        .. code-block:: python

            HourlyPartitionsDefinition(start_date=datetime(2022, 03, 12))
            # creates partitions (2022-03-12-00:00, 2022-03-12-01:00), (2022-03-12-01:00, 2022-03-12-02:00), ...

            HourlyPartitionsDefinition(start_date=datetime(2022, 03, 12), minute_offset=15)
            # creates partitions (2022-03-12-00:15, 2022-03-12-01:15), (2022-03-12-01:15, 2022-03-12-02:15), ...
        """
        _fmt = fmt or DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE

        return super(HourlyPartitionsDefinition, cls).__new__(
            cls,
            schedule_type=ScheduleType.HOURLY,
            start=start_date,
            minute_offset=minute_offset,
            timezone=timezone,
            fmt=_fmt,
            end_offset=end_offset,
        )


def hourly_partitioned_config(
    start_date: Union[datetime, str],
    minute_offset: int = 0,
    timezone: Optional[str] = None,
    fmt: Optional[str] = None,
    end_offset: int = 0,
    tags_for_partition_fn: Optional[Callable[[datetime, datetime], Mapping[str, str]]] = None,
) -> Callable[[Callable[[datetime, datetime], Mapping[str, Any]]], PartitionedConfig]:
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

    .. code-block:: python

        @hourly_partitioned_config(start_date=datetime(2022, 03, 12))
        # creates partitions (2022-03-12-00:00, 2022-03-12-01:00), (2022-03-12-01:00, 2022-03-12-02:00), ...

        @hourly_partitioned_config(start_date=datetime(2022, 03, 12), minute_offset=15)
        # creates partitions (2022-03-12-00:15, 2022-03-12-01:15), (2022-03-12-01:15, 2022-03-12-02:15), ...
    """

    def inner(fn: Callable[[datetime, datetime], Mapping[str, Any]]) -> PartitionedConfig:
        check.callable_param(fn, "fn")

        return PartitionedConfig(
            run_config_for_partition_fn=lambda partition: fn(
                partition.value[0], partition.value[1]
            ),
            partitions_def=HourlyPartitionsDefinition(
                start_date=start_date,
                minute_offset=minute_offset,
                timezone=timezone,
                fmt=fmt,
                end_offset=end_offset,
            ),
            decorated_fn=fn,
            tags_for_partition_fn=wrap_time_window_tags_fn(tags_for_partition_fn),
        )

    return inner


class MonthlyPartitionsDefinition(TimeWindowPartitionsDefinition):
    def __new__(  # pylint: disable=signature-differs
        cls,
        start_date: Union[datetime, str],
        minute_offset: int = 0,
        hour_offset: int = 0,
        day_offset: int = 1,
        timezone: Optional[str] = None,
        fmt: Optional[str] = None,
        end_offset: int = 0,
    ):
        """A set of monthly partitions.

        The first partition in the set will start at the soonest first of the month after start_date
        at midnight. The last partition in the set will end before the current time, unless the
        end_offset argument is set to a positive number. If day_offset is provided, the start and
        end date of each partition will be day_offset. If minute_offset and/or hour_offset are used,
        the start and end times of each partition will be hour_offset:minute_offset of each day.

        Args:
            start_date (Union[datetime.datetime, str]): The first date in the set of partitions will be
                midnight the sonnest first of the month following start_date. Can provide in either a
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

        .. code-block:: python

            MonthlyPartitionsDefinition(start_date="2022-03-12")
            # creates partitions (2022-04-01-00:00, 2022-05-01-00:00), (2022-05-01-00:00, 2022-06-01-00:00), ...

            MonthlyPartitionsDefinition(start_date="2022-03-12", minute_offset=15, hour_offset=3, day_offset=5)
            # creates partitions (2022-04-05-03:15, 2022-05-05-03:15), (2022-05-05-03:15, 2022-06-05-03:15), ...
        """
        _fmt = fmt or DEFAULT_DATE_FORMAT

        return super(MonthlyPartitionsDefinition, cls).__new__(
            cls,
            schedule_type=ScheduleType.MONTHLY,
            start=start_date,
            minute_offset=minute_offset,
            hour_offset=hour_offset,
            day_offset=day_offset,
            timezone=timezone,
            fmt=_fmt,
            end_offset=end_offset,
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
) -> Callable[[Callable[[datetime, datetime], Mapping[str, Any]]], PartitionedConfig]:
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
            midnight the sonnest first of the month following start_date. Can provide in either a
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

    .. code-block:: python

        @monthly_partitioned_config(start_date="2022-03-12")
        # creates partitions (2022-04-01-00:00, 2022-05-01-00:00), (2022-05-01-00:00, 2022-06-01-00:00), ...

        @monthly_partitioned_config(start_date="2022-03-12", minute_offset=15, hour_offset=3, day_offset=5)
        # creates partitions (2022-04-05-03:15, 2022-05-05-03:15), (2022-05-05-03:15, 2022-06-05-03:15), ...
    """

    def inner(fn: Callable[[datetime, datetime], Mapping[str, Any]]) -> PartitionedConfig:
        check.callable_param(fn, "fn")

        return PartitionedConfig(
            run_config_for_partition_fn=lambda partition: fn(
                partition.value[0], partition.value[1]
            ),
            partitions_def=MonthlyPartitionsDefinition(
                start_date=start_date,
                minute_offset=minute_offset,
                hour_offset=hour_offset,
                day_offset=day_offset,
                timezone=timezone,
                fmt=fmt,
                end_offset=end_offset,
            ),
            decorated_fn=fn,
            tags_for_partition_fn=wrap_time_window_tags_fn(tags_for_partition_fn),
        )

    return inner


class WeeklyPartitionsDefinition(TimeWindowPartitionsDefinition):
    def __new__(  # pylint: disable=signature-differs
        cls,
        start_date: Union[datetime, str],
        minute_offset: int = 0,
        hour_offset: int = 0,
        day_offset: int = 0,
        timezone: Optional[str] = None,
        fmt: Optional[str] = None,
        end_offset: int = 0,
    ):
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
        _fmt = fmt or DEFAULT_DATE_FORMAT

        return super(WeeklyPartitionsDefinition, cls).__new__(
            cls,
            schedule_type=ScheduleType.WEEKLY,
            start=start_date,
            minute_offset=minute_offset,
            hour_offset=hour_offset,
            day_offset=day_offset,
            timezone=timezone,
            fmt=_fmt,
            end_offset=end_offset,
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
) -> Callable[[Callable[[datetime, datetime], Mapping[str, Any]]], PartitionedConfig]:
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

    .. code-block:: python

        @weekly_partitioned_config(start_date="2022-03-12")
        # creates partitions (2022-03-13-00:00, 2022-03-20-00:00), (2022-03-20-00:00, 2022-03-27-00:00), ...

        @weekly_partitioned_config(start_date="2022-03-12", minute_offset=15, hour_offset=3, day_offset=6)
        # creates partitions (2022-03-12-03:15, 2022-03-19-03:15), (2022-03-19-03:15, 2022-03-26-03:15), ...
    """

    def inner(fn: Callable[[datetime, datetime], Mapping[str, Any]]) -> PartitionedConfig:
        check.callable_param(fn, "fn")

        return PartitionedConfig(
            run_config_for_partition_fn=lambda partition: fn(
                partition.value[0], partition.value[1]
            ),
            partitions_def=WeeklyPartitionsDefinition(
                start_date=start_date,
                minute_offset=minute_offset,
                hour_offset=hour_offset,
                day_offset=day_offset,
                timezone=timezone,
                fmt=fmt,
                end_offset=end_offset,
            ),
            decorated_fn=fn,
            tags_for_partition_fn=wrap_time_window_tags_fn(tags_for_partition_fn),
        )

    return inner


class TimeWindowPartitionsSubset(PartitionsSubset):
    # Every time we change the serialization format, we should increment the version number.
    # This will ensure that we can gracefully degrade when deserializing old data.
    SERIALIZATION_VERSION = 1

    def __init__(
        self,
        partitions_def: TimeWindowPartitionsDefinition,
        included_time_windows: Sequence[TimeWindow],
        num_partitions: int,
    ):
        self._partitions_def = check.inst_param(
            partitions_def, "partitions_def", TimeWindowPartitionsDefinition
        )
        check.sequence_param(included_time_windows, "included_time_windows", of_type=TimeWindow)
        self._included_time_windows = included_time_windows
        self._num_partitions = num_partitions

    def _get_partition_time_windows_not_in_subset(
        self,
        current_time: Optional[datetime] = None,
    ) -> Sequence[TimeWindow]:
        """
        Returns a list of partition time windows that are not in the subset.
        Each time window is a single partition.
        """
        first_tw = self._partitions_def.get_first_partition_window()
        last_tw = self._partitions_def.get_last_partition_window(current_time=current_time)

        if not first_tw or not last_tw:
            check.failed("No partitions found")

        if len(self._included_time_windows) == 0:
            return [TimeWindow(first_tw.start, last_tw.end)]

        time_windows = []
        if first_tw.start < self._included_time_windows[0].start:
            time_windows.append(TimeWindow(first_tw.start, self._included_time_windows[0].start))

        for i in range(len(self._included_time_windows) - 1):
            if self._included_time_windows[i].start >= last_tw.end:
                break
            if self._included_time_windows[i].end < last_tw.end:
                if self._included_time_windows[i + 1].start <= last_tw.end:
                    time_windows.append(
                        TimeWindow(
                            self._included_time_windows[i].end,
                            self._included_time_windows[i + 1].start,
                        )
                    )
                else:
                    time_windows.append(
                        TimeWindow(
                            self._included_time_windows[i].end,
                            last_tw.end,
                        )
                    )

        if last_tw.end > self._included_time_windows[-1].end:
            time_windows.append(TimeWindow(self._included_time_windows[-1].end, last_tw.end))

        return time_windows

    def get_partition_keys_not_in_subset(
        self, current_time: Optional[datetime] = None
    ) -> Iterable[str]:
        partition_keys: List[str] = []
        for tw in self._get_partition_time_windows_not_in_subset(current_time):
            partition_keys.extend(self._partitions_def.get_partition_keys_in_time_window(tw))
        return partition_keys

    def get_partition_keys(self, current_time: Optional[datetime] = None) -> Iterable[str]:
        return [
            pk
            for time_window in self._included_time_windows
            for pk in self._partitions_def.get_partition_keys_in_time_window(time_window)
        ]

    def get_partition_key_ranges(
        self, current_time: Optional[datetime] = None
    ) -> Sequence[PartitionKeyRange]:
        return [
            self._partitions_def.get_partition_key_range_for_time_window(window)
            for window in self._included_time_windows
        ]

    @property
    def included_time_windows(self) -> Sequence[TimeWindow]:
        return self._included_time_windows

    def with_partition_keys(self, partition_keys: Iterable[str]) -> "TimeWindowPartitionsSubset":
        result_windows = [*self._included_time_windows]
        time_windows = self._partitions_def.time_windows_for_partition_keys(
            list(partition_keys),
        )
        num_added_partitions = 0
        for window in sorted(time_windows):
            # go in reverse order because it's more common to add partitions at the end than the
            # beginning
            for i in reversed(range(len(result_windows))):
                included_window = result_windows[i]
                lt_end_of_range = window.start < included_window.end
                gte_start_of_range = window.start >= included_window.start

                if lt_end_of_range and gte_start_of_range:
                    break

                if not lt_end_of_range:
                    merge_with_range = included_window.end == window.start
                    merge_with_later_range = i + 1 < len(result_windows) and (
                        window.end == result_windows[i + 1].start
                    )

                    if merge_with_range and merge_with_later_range:
                        result_windows[i] = TimeWindow(
                            included_window.start, result_windows[i + 1].end
                        )
                        del result_windows[i + 1]
                    elif merge_with_range:
                        result_windows[i] = TimeWindow(included_window.start, window.end)
                    elif merge_with_later_range:
                        result_windows[i + 1] = TimeWindow(window.start, result_windows[i + 1].end)
                    else:
                        result_windows.insert(i + 1, window)

                    num_added_partitions += 1
                    break
            else:
                if result_windows and window.start == result_windows[0].start:
                    result_windows[0] = TimeWindow(window.start, included_window.end)
                else:
                    result_windows.insert(0, window)

                num_added_partitions += 1

        return TimeWindowPartitionsSubset(
            self._partitions_def, result_windows, self._num_partitions + num_added_partitions
        )

    def with_partition_key_range(
        self, partition_key_range: PartitionKeyRange
    ) -> "PartitionsSubset":
        return self.with_partition_keys(
            self._partitions_def.get_partition_keys_in_range(partition_key_range)
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
                TimeWindow(
                    pendulum.from_timestamp(tup[0], tz=partitions_def.timezone),
                    pendulum.from_timestamp(tup[1], tz=partitions_def.timezone),
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

        return TimeWindowPartitionsSubset(partitions_def, time_windows, num_partitions)

    def serialize(self) -> str:
        return json.dumps(
            {
                "version": self.SERIALIZATION_VERSION,
                "time_windows": [
                    (window.start.timestamp(), window.end.timestamp())
                    for window in self._included_time_windows
                ],
                "num_partitions": self._num_partitions,
            }
        )

    @property
    def partitions_def(self) -> PartitionsDefinition:
        return self._partitions_def

    def __eq__(self, other):
        return (
            isinstance(other, TimeWindowPartitionsSubset)
            and self._partitions_def == other._partitions_def
            and self._included_time_windows == other._included_time_windows
        )

    def __len__(self) -> int:
        return self._num_partitions

    def __contains__(self, partition_key: str) -> bool:
        time_window = self._partitions_def.time_window_for_partition_key(partition_key)

        return any(
            time_window.start >= included_time_window.start
            and time_window.start < included_time_window.end
            for included_time_window in self._included_time_windows
        )
