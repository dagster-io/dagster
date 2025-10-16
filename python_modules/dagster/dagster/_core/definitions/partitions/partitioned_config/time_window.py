from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any, Callable, Optional, Union

import dagster._check as check
from dagster._annotations import public
from dagster._core.definitions.partitions.definition.time_window import (
    TimeWindowPartitionsDefinition,
)
from dagster._core.definitions.partitions.definition.time_window_subclasses import (
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
    MonthlyPartitionsDefinition,
    WeeklyPartitionsDefinition,
)
from dagster._core.definitions.partitions.partitioned_config import PartitionedConfig
from dagster._core.definitions.timestamp import TimestampWithTimezone


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


@public
def hourly_partitioned_config(
    start_date: Union[datetime, str],
    minute_offset: int = 0,
    timezone: Optional[str] = None,
    fmt: Optional[str] = None,
    end_offset: int = 0,
    tags_for_partition_fn: Optional[Callable[[datetime, datetime], Mapping[str, str]]] = None,
    exclusions: Optional[Sequence[Union[str, datetime, TimestampWithTimezone]]] = None,
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
            `IANA time zone database <https://www.iana.org/time-zones>`_ - e.g. "America/Los_Angeles".
        end_offset (int): Extends the partition set by a number of partitions equal to the value
            passed. If end_offset is 0 (the default), the last partition ends before the current
            time. If end_offset is 1, the second-to-last partition ends before the current time,
            and so on.
        tags_for_partition_fn (Optional[Callable[[str], Mapping[str, str]]]): A function that
            accepts a partition time window and returns a dictionary of tags to attach to runs for
            that partition.
        exclusions (Optional[Sequence[Union[str, datetime]]]): Specifies a sequence of cron strings
            or datetime objects that should be excluded from the partition set. Every tick of the
            cron schedule that matches an excluded datetime or matches the tick of an excluded
            cron string will be excluded from the partition set.

    .. code-block:: python

        from datetime import datetime
        from dagster import hourly_partitioned_config

        @hourly_partitioned_config(start_date=datetime(2022, 3, 12))
        def my_hourly_partitioned_config(start: datetime, end: datetime):
            return {"start": start.strftime("%Y-%m-%d %H:%M"), "end": end.strftime("%Y-%m-%d %H:%M")}
        # creates partitions (2022-03-12-00:00, 2022-03-12-01:00), (2022-03-12-01:00, 2022-03-12-02:00), ...

        @hourly_partitioned_config(start_date=datetime(2022, 3, 12), minute_offset=15)
        def my_offset_hourly_partitioned_config(start: datetime, end: datetime):
            return {"start": start.strftime("%Y-%m-%d %H:%M"), "end": end.strftime("%Y-%m-%d %H:%M")}
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
            exclusions=exclusions,
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


@public
def daily_partitioned_config(
    start_date: Union[datetime, str],
    minute_offset: int = 0,
    hour_offset: int = 0,
    timezone: Optional[str] = None,
    fmt: Optional[str] = None,
    end_offset: int = 0,
    tags_for_partition_fn: Optional[Callable[[datetime, datetime], Mapping[str, str]]] = None,
    exclusions: Optional[Sequence[Union[str, datetime, TimestampWithTimezone]]] = None,
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
            `IANA time zone database <https://www.iana.org/time-zones>`_ - e.g. "America/Los_Angeles".
        fmt (Optional[str]): The date format to use. Defaults to `%Y-%m-%d`.
        end_offset (int): Extends the partition set by a number of partitions equal to the value
            passed. If end_offset is 0 (the default), the last partition ends before the current
            time. If end_offset is 1, the second-to-last partition ends before the current time,
            and so on.
        tags_for_partition_fn (Optional[Callable[[str], Mapping[str, str]]]): A function that
            accepts a partition time window and returns a dictionary of tags to attach to runs for
            that partition.
        exclusions (Optional[Sequence[Union[str, datetime]]]): Specifies a sequence of cron strings
            or datetime objects that should be excluded from the partition set. Every tick of the
            cron schedule that matches an excluded datetime or matches the tick of an excluded
            cron string will be excluded from the partition set.

    .. code-block:: python

        from datetime import datetime
        from dagster import daily_partitioned_config

        @daily_partitioned_config(start_date="2022-03-12")
        def my_partitioned_config(start: datetime, end: datetime):
            return {"start": start.strftime("%Y-%m-%d"), "end": end.strftime("%Y-%m-%d")}
        # creates partitions (2022-03-12-00:00, 2022-03-13-00:00), (2022-03-13-00:00, 2022-03-14-00:00), ...

        @daily_partitioned_config(start_date="2022-03-12", minute_offset=15, hour_offset=16)
        def my_offset_partitioned_config(start: datetime, end: datetime):
            return {"start": start.strftime("%Y-%m-%d"), "end": end.strftime("%Y-%m-%d")}
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
            exclusions=exclusions,
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


@public
def weekly_partitioned_config(
    start_date: Union[datetime, str],
    minute_offset: int = 0,
    hour_offset: int = 0,
    day_offset: int = 0,
    timezone: Optional[str] = None,
    fmt: Optional[str] = None,
    end_offset: int = 0,
    tags_for_partition_fn: Optional[Callable[[datetime, datetime], Mapping[str, str]]] = None,
    exclusions: Optional[Sequence[Union[str, datetime, TimestampWithTimezone]]] = None,
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
            `IANA time zone database <https://www.iana.org/time-zones>`_ - e.g. "America/Los_Angeles".
        fmt (Optional[str]): The date format to use. Defaults to `%Y-%m-%d`.
        end_offset (int): Extends the partition set by a number of partitions equal to the value
            passed. If end_offset is 0 (the default), the last partition ends before the current
            time. If end_offset is 1, the second-to-last partition ends before the current time,
            and so on.
        tags_for_partition_fn (Optional[Callable[[str], Mapping[str, str]]]): A function that
            accepts a partition time window and returns a dictionary of tags to attach to runs for
            that partition.
        exclusions (Optional[Sequence[Union[str, datetime]]]): Specifies a sequence of cron strings
            or datetime objects that should be excluded from the partition set. Every tick of the
            cron schedule that matches an excluded datetime or matches the tick of an excluded
            cron string will be excluded from the partition set.

    .. code-block:: python

        from datetime import datetime
        from dagster import weekly_partitioned_config

        @weekly_partitioned_config(start_date="2022-03-12")
        def my_weekly_partitioned_config(start: datetime, end: datetime):
            return {"start": start.strftime("%Y-%m-%d"), "end": end.strftime("%Y-%m-%d")}
        # creates partitions (2022-03-13-00:00, 2022-03-20-00:00), (2022-03-20-00:00, 2022-03-27-00:00), ...

        @weekly_partitioned_config(start_date="2022-03-12", minute_offset=15, hour_offset=3, day_offset=6)
        def my_offset_weekly_partitioned_config(start: datetime, end: datetime):
            return {"start": start.strftime("%Y-%m-%d"), "end": end.strftime("%Y-%m-%d")}
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
            exclusions=exclusions,
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


@public
def monthly_partitioned_config(
    start_date: Union[datetime, str],
    minute_offset: int = 0,
    hour_offset: int = 0,
    day_offset: int = 1,
    timezone: Optional[str] = None,
    fmt: Optional[str] = None,
    end_offset: int = 0,
    tags_for_partition_fn: Optional[Callable[[datetime, datetime], Mapping[str, str]]] = None,
    exclusions: Optional[Sequence[Union[str, datetime, TimestampWithTimezone]]] = None,
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
            `IANA time zone database <https://www.iana.org/time-zones>`_ - e.g. "America/Los_Angeles".
        fmt (Optional[str]): The date format to use. Defaults to `%Y-%m-%d`.
        end_offset (int): Extends the partition set by a number of partitions equal to the value
            passed. If end_offset is 0 (the default), the last partition ends before the current
            time. If end_offset is 1, the second-to-last partition ends before the current time,
            and so on.
        tags_for_partition_fn (Optional[Callable[[str], Mapping[str, str]]]): A function that
            accepts a partition time window and returns a dictionary of tags to attach to runs for
            that partition.
        exclusions (Optional[Sequence[Union[str, datetime]]]): Specifies a sequence of cron strings
            or datetime objects that should be excluded from the partition set. Every tick of the
            cron schedule that matches an excluded datetime or matches the tick of an excluded
            cron string will be excluded from the partition set.

    .. code-block:: python

        from datetime import datetime
        from dagster import monthly_partitioned_config

        @monthly_partitioned_config(start_date="2022-03-12")
        def my_monthly_partitioned_config(start: datetime, end: datetime):
            return {"start": start.strftime("%Y-%m-%d"), "end": end.strftime("%Y-%m-%d")}
        # creates partitions (2022-04-01-00:00, 2022-05-01-00:00), (2022-05-01-00:00, 2022-06-01-00:00), ...

        @monthly_partitioned_config(start_date="2022-03-12", minute_offset=15, hour_offset=3, day_offset=5)
        def my_offset_monthly_partitioned_config(start: datetime, end: datetime):
            return {"start": start.strftime("%Y-%m-%d"), "end": end.strftime("%Y-%m-%d")}
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
            exclusions=exclusions,
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
