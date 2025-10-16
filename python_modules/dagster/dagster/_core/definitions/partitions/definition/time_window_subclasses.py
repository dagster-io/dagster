from collections.abc import Sequence
from datetime import datetime
from typing import Optional, Union

import dagster._check as check
from dagster._annotations import public
from dagster._core.definitions.partitions.definition.time_window import (
    TimeWindowPartitionsDefinition,
)
from dagster._core.definitions.partitions.schedule_type import ScheduleType
from dagster._core.definitions.timestamp import TimestampWithTimezone
from dagster._utils.partitions import DEFAULT_DATE_FORMAT, DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE


@public
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
            `IANA time zone database <https://www.iana.org/time-zones>`_ - e.g. "America/Los_Angeles".
        end_offset (int): Extends the partition set by a number of partitions equal to the value
            passed. If end_offset is 0 (the default), the last partition ends before the current
            time. If end_offset is 1, the second-to-last partition ends before the current time,
            and so on.
        exclusions (Optional[Sequence[Union[str, datetime]]]): Specifies a sequence of cron strings
            or datetime objects that should be excluded from the partition set. Every tick of the
            cron schedule that matches an excluded datetime or matches the tick of an excluded
            cron string will be excluded from the partition set.

    .. code-block:: python

        from datetime import datetime
        from dagster import HourlyPartitionsDefinition

        # Basic hourly partitions starting at midnight
        hourly_partitions = HourlyPartitionsDefinition(start_date=datetime(2022, 3, 12))

        # Hourly partitions with 15-minute offset
        offset_partitions = HourlyPartitionsDefinition(
            start_date=datetime(2022, 3, 12),
            minute_offset=15
        )
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
        exclusions: Optional[Sequence[Union[str, datetime, TimestampWithTimezone]]] = None,
        **kwargs,
    ):
        _fmt = fmt or DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE
        schedule_type = ScheduleType.HOURLY

        # We accept cron_schedule "hidden" via kwargs to support record copy()
        cron_schedule = kwargs.get("cron_schedule")
        if cron_schedule:
            schedule_type = None

        return super().__new__(
            cls,
            schedule_type=schedule_type,
            start=start_date,
            end=end_date,
            minute_offset=minute_offset,
            timezone=timezone,
            fmt=_fmt,
            end_offset=end_offset,
            cron_schedule=cron_schedule,
            exclusions=exclusions,
        )


@public
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
            `IANA time zone database <https://www.iana.org/time-zones>`_ - e.g. "America/Los_Angeles".
        fmt (Optional[str]): The date format to use. Defaults to `%Y-%m-%d`.
        end_offset (int): Extends the partition set by a number of partitions equal to the value
            passed. If end_offset is 0 (the default), the last partition ends before the current
            time. If end_offset is 1, the second-to-last partition ends before the current time,
            and so on.
        exclusions (Optional[Sequence[Union[str, datetime]]]): Specifies a sequence of cron strings
            or datetime objects that should be excluded from the partition set. Every tick of the
            cron schedule that matches an excluded datetime or matches the tick of an excluded
            cron string will be excluded from the partition set.

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
        exclusions: Optional[Sequence[Union[str, datetime, TimestampWithTimezone]]] = None,
        **kwargs,
    ):
        _fmt = fmt or DEFAULT_DATE_FORMAT

        schedule_type = ScheduleType.DAILY

        # We accept cron_schedule "hidden" via kwargs to support record copy()
        cron_schedule = kwargs.get("cron_schedule")
        if cron_schedule:
            schedule_type = None

        return super().__new__(
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
            exclusions=exclusions,
        )


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
            `IANA time zone database <https://www.iana.org/time-zones>`_ - e.g. "America/Los_Angeles".
        fmt (Optional[str]): The date format to use. Defaults to `%Y-%m-%d`.
        end_offset (int): Extends the partition set by a number of partitions equal to the value
            passed. If end_offset is 0 (the default), the last partition ends before the current
            time. If end_offset is 1, the second-to-last partition ends before the current time,
            and so on.
        exclusions (Optional[Sequence[Union[str, datetime]]]): Specifies a sequence of cron strings
            or datetime objects that should be excluded from the partition set. Every tick of the
            cron schedule that matches an excluded datetime or matches the tick of an excluded
            cron string will be excluded from the partition set.

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
        exclusions: Optional[Sequence[Union[str, datetime, TimestampWithTimezone]]] = None,
        **kwargs,
    ):
        _fmt = fmt or DEFAULT_DATE_FORMAT
        schedule_type = ScheduleType.WEEKLY
        # We accept cron_schedule "hidden" via kwargs to support record copy()
        cron_schedule = kwargs.get("cron_schedule")
        if cron_schedule:
            schedule_type = None

        return super().__new__(
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
            exclusions=exclusions,
        )


@public
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
            `IANA time zone database <https://www.iana.org/time-zones>`_ - e.g. "America/Los_Angeles".
        fmt (Optional[str]): The date format to use. Defaults to `%Y-%m-%d`.
        end_offset (int): Extends the partition set by a number of partitions equal to the value
            passed. If end_offset is 0 (the default), the last partition ends before the current
            time. If end_offset is 1, the second-to-last partition ends before the current time,
            and so on.
        exclusions (Optional[Sequence[Union[str, datetime]]]): Specifies a sequence of cron strings
            or datetime objects that should be excluded from the partition set. Every tick of the
            cron schedule that matches an excluded datetime or matches the tick of an excluded
            cron string will be excluded from the partition set.

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
        exclusions: Optional[Sequence[Union[str, datetime, TimestampWithTimezone]]] = None,
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

        return super().__new__(
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
            exclusions=exclusions,
        )
