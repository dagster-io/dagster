from datetime import datetime
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Union

import pendulum
from dagster import check
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
        ],
    ),
):
    def __new__(
        cls, schedule_type: ScheduleType, start: datetime, timezone: str, fmt: str, end_offset: int
    ):
        check.param_invariant(end_offset >= 0, "end_offset", "end_offset must be non-negative")
        return super(TimeWindowPartitionsDefinition, cls).__new__(
            cls, schedule_type, start, timezone, fmt, end_offset
        )

    def get_partitions(
        self, current_time: Optional[datetime] = None
    ) -> List[Partition[TimeWindow]]:
        current_timestamp = (
            pendulum.instance(current_time, tz=self.timezone)
            if current_time
            else pendulum.now(self.timezone)
        ).timestamp()

        start_timestamp = pendulum.instance(self.start, tz=self.timezone).timestamp()
        iterator = schedule_execution_time_iterator(
            start_timestamp=start_timestamp,
            cron_schedule=get_cron_schedule(schedule_type=self.schedule_type),
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

        return partitions


def daily_partitioned_config(
    start_date: Union[datetime, str],
    timezone: Optional[str] = None,
    fmt: Optional[str] = None,
    end_offset: int = 0,
) -> Callable[[Callable[[datetime, datetime], Dict[str, Any]]], PartitionedConfig]:
    """Defines run config over a set of daily partitions.

    The decorated function should accept a start datetime and end datetime, which represent the bounds
    of the date partition the config should delineate.

    The decorated function should return a run config dictionary.

    The resulting object created by this decorator can be provided to the config argument of a Job.
    The first partition in the set will start at the start_date. The last partition in the set will
    end before the current time, unless the end_offset argument is set to a positive number.

    Args:
        start_date (Union[datetime.datetime, str]): The date from which to run the schedule. Can
            provide in either a datetime or string format.
        timezone (Optional[str]): The timezone in which each date should exist.
            Supported strings for timezones are the ones provided by the
            `IANA time zone database <https://www.iana.org/time-zones>` - e.g. "America/Los_Angeles".
        fmt (Optional[str]): The date format to use. Defaults to `%Y-%m-%d`.
        end_offset (int): Extends the partition set by a number of partitions equal to the value
            passed. If end_offset is 0 (the default), the last partition ends before the current
            time. If end_offset is 1, the second-to-last partition ends before the current time,
            and so on.
    """
    _fmt = fmt or DEFAULT_DATE_FORMAT
    _timezone = timezone or "UTC"

    if isinstance(start_date, str):
        _start_date = datetime.strptime(start_date, _fmt)
    else:
        _start_date = start_date

    def inner(fn: Callable[[datetime, datetime], Dict[str, Any]]) -> PartitionedConfig:
        check.callable_param(fn, "fn")

        return PartitionedConfig(
            run_config_for_partition_fn=lambda partition: fn(
                partition.value[0], partition.value[1]
            ),
            partitions_def=TimeWindowPartitionsDefinition(
                schedule_type=ScheduleType.DAILY,
                start=_start_date,
                timezone=_timezone,
                fmt=_fmt,
                end_offset=end_offset,
            ),
        )

    return inner


def hourly_partitioned_config(
    start_date: Union[datetime, str],
    timezone: Optional[str] = None,
    fmt: Optional[str] = None,
    end_offset: int = 0,
) -> Callable[[Callable[[datetime, datetime], Dict[str, Any]]], PartitionedConfig]:
    """Defines run config over a set of hourly partitions.

    The decorated function should accept a start datetime and end datetime, which represent the date
    partition the config should delineate.

    The decorated function should return a run config dictionary.

    The resulting object created by this decorator can be provided to the config argument of a Job.
    The first partition in the set will start at the start_date. The last partition in the set will
    end before the current time, unless the end_offset argument is set to a positive number.

    Args:
        start_date (Union[datetime.datetime, str]): The date from which to run the schedule. Can
            provide in either a datetime or string format.
        fmt (Optional[str]): The date format to use. Defaults to `%Y-%m-%d`.
        timezone (Optional[str]): The timezone in which each date should exist.
            Supported strings for timezones are the ones provided by the
            `IANA time zone database <https://www.iana.org/time-zones>` - e.g. "America/Los_Angeles".
        end_offset (int): Extends the partition set by a number of partitions equal to the value
            passed. If end_offset is 0 (the default), the last partition ends before the current
            time. If end_offset is 1, the second-to-last partition ends before the current time,
            and so on.
    """
    _fmt = fmt or DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE
    _timezone = timezone or "UTC"

    if isinstance(start_date, str):
        _start_date = datetime.strptime(start_date, _fmt)
    else:
        _start_date = start_date

    def inner(fn: Callable[[datetime, datetime], Dict[str, Any]]) -> PartitionedConfig:
        check.callable_param(fn, "fn")

        return PartitionedConfig(
            run_config_for_partition_fn=lambda partition: fn(
                partition.value[0], partition.value[1]
            ),
            partitions_def=TimeWindowPartitionsDefinition(
                schedule_type=ScheduleType.HOURLY,
                start=_start_date,
                timezone=_timezone,
                fmt=_fmt,
                end_offset=end_offset,
            ),
        )

    return inner


def monthly_partitioned_config(
    start_date: Union[datetime, str],
    timezone: Optional[str] = None,
    fmt: Optional[str] = None,
    end_offset: int = 0,
) -> Callable[[Callable[[datetime, datetime], Dict[str, Any]]], PartitionedConfig]:
    """Defines run config over a set of monthly partitions.

    The decorated function should accept a start datetime and end datetime, which represent the date
    partition the config should delineate.

    The decorated function should return a run config dictionary.

    The resulting object created by this decorator can be provided to the config argument of a Job.
    The first partition in the set will start at the start_date. The last partition in the set will
    end before the current time, unless the end_offset argument is set to a positive number.

    Args:
        start_date (Union[datetime.datetime, str]): The date from which to run the schedule. Can
            provide in either a datetime or string format.
        timezone (Optional[str]): The timezone in which each date should exist.
            Supported strings for timezones are the ones provided by the
            `IANA time zone database <https://www.iana.org/time-zones>` - e.g. "America/Los_Angeles".
        fmt (Optional[str]): The date format to use. Defaults to `%Y-%m-%d`.
        end_offset (int): Extends the partition set by a number of partitions equal to the value
            passed. If end_offset is 0 (the default), the last partition ends before the current
            time. If end_offset is 1, the second-to-last partition ends before the current time,
            and so on.
    """
    _fmt = fmt or DEFAULT_DATE_FORMAT
    _timezone = timezone or "UTC"

    if isinstance(start_date, str):
        _start_date = datetime.strptime(start_date, _fmt)
    else:
        _start_date = start_date

    def inner(fn: Callable[[datetime, datetime], Dict[str, Any]]) -> PartitionedConfig:
        check.callable_param(fn, "fn")

        return PartitionedConfig(
            run_config_for_partition_fn=lambda partition: fn(
                partition.value[0], partition.value[1]
            ),
            partitions_def=TimeWindowPartitionsDefinition(
                schedule_type=ScheduleType.MONTHLY,
                start=_start_date,
                timezone=_timezone,
                fmt=_fmt,
                end_offset=end_offset,
            ),
        )

    return inner


def weekly_partitioned_config(
    start_date: Union[datetime, str],
    timezone: Optional[str] = None,
    fmt: Optional[str] = None,
    end_offset: int = 0,
) -> Callable[[Callable[[datetime, datetime], Dict[str, Any]]], PartitionedConfig]:
    """Defines run config over a set of weekly partitions.

    The decorated function should accept a start datetime and end datetime, which represent the date
    partition the config should delineate.

    The decorated function should return a run config dictionary.

    The resulting object created by this decorator can be provided to the config argument of a Job.
    The first partition in the set will start at the start_date. The last partition in the set will
    end before the current time, unless the end_offset argument is set to a positive number.

    Args:
        start_date (Union[datetime.datetime, str]): The date from which to run the schedule. Can
            provide in either a datetime or string format.
        timezone (Optional[str]): The timezone in which each date should exist.
            Supported strings for timezones are the ones provided by the
            `IANA time zone database <https://www.iana.org/time-zones>` - e.g. "America/Los_Angeles".
        fmt (Optional[str]): The date format to use. Defaults to `%Y-%m-%d`.
        end_offset (int): Extends the partition set by a number of partitions equal to the value
            passed. If end_offset is 0 (the default), the last partition ends before the current
            time. If end_offset is 1, the second-to-last partition ends before the current time,
            and so on.
    """
    _fmt = fmt or DEFAULT_DATE_FORMAT
    _timezone = timezone or "UTC"

    if isinstance(start_date, str):
        _start_date = datetime.strptime(start_date, _fmt)
    else:
        _start_date = start_date

    def inner(fn: Callable[[datetime, datetime], Dict[str, Any]]) -> PartitionedConfig:
        check.callable_param(fn, "fn")

        return PartitionedConfig(
            run_config_for_partition_fn=lambda partition: fn(
                partition.value[0], partition.value[1]
            ),
            partitions_def=TimeWindowPartitionsDefinition(
                schedule_type=ScheduleType.WEEKLY,
                start=_start_date,
                timezone=_timezone,
                fmt=_fmt,
                end_offset=end_offset,
            ),
        )

    return inner
