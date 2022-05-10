from datetime import datetime, time
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Union, cast

import pendulum

import dagster._check as check
from dagster.utils.partitions import DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE
from dagster.utils.schedules import schedule_execution_time_iterator

from .partition import (
    DEFAULT_DATE_FORMAT,
    Partition,
    PartitionedConfig,
    PartitionsDefinition,
    ScheduleType,
    get_cron_schedule,
)


class TimeWindow(NamedTuple):
    """An interval that is closed at the start and open at the end"""

    start: datetime
    end: datetime


class TimeWindowPartitionsDefinition(
    PartitionsDefinition[TimeWindow],  # pylint: disable=unsubscriptable-object
    NamedTuple(
        "_TimeWindowPartitions",
        [
            ("schedule_type", ScheduleType),
            ("start", datetime),
            ("timezone", str),
            ("fmt", str),
            ("end_offset", int),
            ("minute_offset", int),
            ("hour_offset", int),
            ("day_offset", Optional[int]),
        ],
    ),
):
    def __new__(  # pylint: disable=arguments-differ
        cls,
        schedule_type: ScheduleType,
        start: Union[datetime, str],
        timezone: Optional[str],
        fmt: str,
        end_offset: int,
        minute_offset: int = 0,
        hour_offset: int = 0,
        day_offset: Optional[int] = None,
    ):
        if isinstance(start, str):
            start_dt = datetime.strptime(start, fmt)
        else:
            start_dt = start

        return super(TimeWindowPartitionsDefinition, cls).__new__(
            cls,
            schedule_type,
            start_dt,
            timezone or "UTC",
            fmt,
            end_offset,
            minute_offset,
            hour_offset,
            day_offset,
        )

    def get_partitions(
        self, current_time: Optional[datetime] = None
    ) -> List[Partition[TimeWindow]]:
        current_timestamp = (
            pendulum.instance(current_time, tz=self.timezone)
            if current_time
            else pendulum.now(self.timezone)
        ).timestamp()

        time_of_day = time(self.hour_offset, self.minute_offset)

        start_timestamp = pendulum.instance(self.start, tz=self.timezone).timestamp()
        iterator = schedule_execution_time_iterator(
            start_timestamp=start_timestamp,
            cron_schedule=get_cron_schedule(
                schedule_type=self.schedule_type,
                time_of_day=time_of_day,
                execution_day=self.day_offset,
            ),
            execution_timezone=self.timezone,
        )

        partitions: List[Partition[TimeWindow]] = []
        prev_time = next(iterator)
        while prev_time.timestamp() < start_timestamp:
            prev_time = next(iterator)

        end_offset = self.end_offset
        partitions_past_current_time = 0
        while True:
            next_time = next(iterator)
            if (
                next_time.timestamp() <= current_timestamp
                or partitions_past_current_time < end_offset
            ):
                partitions.append(
                    Partition(
                        value=TimeWindow(prev_time, next_time),
                        name=prev_time.strftime(self.fmt),
                    )
                )

                if next_time.timestamp() > current_timestamp:
                    partitions_past_current_time += 1
            else:
                break

            prev_time = next_time

        if end_offset < 0:
            partitions = partitions[:end_offset]

        return partitions

    def __str__(self) -> str:
        partition_def_str = f"{self.schedule_type.value.capitalize()}, starting {self.start.strftime(self.fmt)} {self.timezone}."
        if self.end_offset != 0:
            partition_def_str += f" End offsetted by {self.end_offset} partition{'' if self.end_offset == 1 else 's'}."
        return partition_def_str

    def time_window_for_partition_key(self, partition_key: str) -> TimeWindow:
        start = self.start_time_for_partition_key(partition_key)
        time_of_day = time(self.hour_offset, self.minute_offset)
        iterator = schedule_execution_time_iterator(
            start_timestamp=start.timestamp(),
            cron_schedule=get_cron_schedule(
                schedule_type=self.schedule_type,
                time_of_day=time_of_day,
                execution_day=self.day_offset,
            ),
            execution_timezone=self.timezone,
        )

        return TimeWindow(next(iterator), next(iterator))

    def start_time_for_partition_key(self, partition_key: str) -> datetime:
        return pendulum.instance(datetime.strptime(partition_key, self.fmt), tz=self.timezone)

    def get_default_partition_mapping(self):
        from dagster.core.asset_defs.time_window_partition_mapping import TimeWindowPartitionMapping

        return TimeWindowPartitionMapping()


class DailyPartitionsDefinition(TimeWindowPartitionsDefinition):
    def __new__(
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
    tags_fn: Optional[Callable[[datetime, datetime], Dict[str, str]]]
) -> Callable[[Partition], Dict[str, str]]:
    def _tag_wrapper(partition: Partition) -> Dict[str, str]:
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
    tags_for_partition_fn: Optional[Callable[[datetime, datetime], Dict[str, str]]] = None,
) -> Callable[[Callable[[datetime, datetime], Dict[str, Any]]], PartitionedConfig]:
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

    def inner(fn: Callable[[datetime, datetime], Dict[str, Any]]) -> PartitionedConfig:
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
    def __new__(
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
    tags_for_partition_fn: Optional[Callable[[datetime, datetime], Dict[str, str]]] = None,
) -> Callable[[Callable[[datetime, datetime], Dict[str, Any]]], PartitionedConfig]:
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

    def inner(fn: Callable[[datetime, datetime], Dict[str, Any]]) -> PartitionedConfig:
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
    def __new__(
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
    tags_for_partition_fn: Optional[Callable[[datetime, datetime], Dict[str, str]]] = None,
) -> Callable[[Callable[[datetime, datetime], Dict[str, Any]]], PartitionedConfig]:
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

    def inner(fn: Callable[[datetime, datetime], Dict[str, Any]]) -> PartitionedConfig:
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
    def __new__(
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
    tags_for_partition_fn: Optional[Callable[[datetime, datetime], Dict[str, str]]] = None,
) -> Callable[[Callable[[datetime, datetime], Dict[str, Any]]], PartitionedConfig]:
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

    def inner(fn: Callable[[datetime, datetime], Dict[str, Any]]) -> PartitionedConfig:
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
