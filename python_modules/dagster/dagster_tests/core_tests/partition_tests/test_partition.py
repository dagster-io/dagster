from datetime import datetime, time
from typing import Callable, List, Optional

import pytest
from dagster.check import CheckError
from dagster.core.definitions.partition import (
    DynamicPartitionParams,
    Partition,
    ScheduleType,
    StaticPartitionParams,
    TimeBasedPartitionParams,
)
from dagster.utils.partitions import DEFAULT_HOURLY_FORMAT_WITH_TIMEZONE


@pytest.mark.parametrize(
    argnames=["partitions"],
    argvalues=[([Partition("a_partition")],), ([Partition(x) for x in range(10)],)],
)
def test_static_partition_params(partitions: List[Partition]):
    partition_params = StaticPartitionParams(partitions)

    assert partition_params.get_partitions(current_time=None) == partitions


@pytest.mark.parametrize(
    argnames=["schedule_type", "start", "execution_day", "end", "error_message_regex"],
    ids=[
        "start should be before end",
        "hourly partitions, execution day should not be provided",
        "daily partitions, execution day should not be provided",
        "weekly partitions, execution day should be between 0 and 6",
        "monthly partitions, execution day should be between 1 and 31",
    ],
    argvalues=[
        (
            ScheduleType.DAILY,
            datetime(year=2021, month=1, day=3),
            None,
            datetime(year=2021, month=1, day=1),
            r"Selected date range start .* is after date range end",
        ),
        (
            ScheduleType.HOURLY,
            datetime(year=2021, month=1, day=1),
            1,
            datetime(year=2021, month=1, day=3),
            "Execution day should not be provided",
        ),
        (
            ScheduleType.DAILY,
            datetime(year=2021, month=1, day=1),
            1,
            datetime(year=2021, month=1, day=3),
            "Execution day should not be provided",
        ),
        (
            ScheduleType.WEEKLY,
            datetime(year=2021, month=1, day=1),
            7,
            datetime(year=2021, month=2, day=1),
            "Execution day .* must be between 0 and 6",
        ),
        (
            ScheduleType.MONTHLY,
            datetime(year=2021, month=1, day=1),
            0,
            datetime(year=2021, month=2, day=1),
            "Execution day .* must be between 1 and 31",
        ),
    ],
)
def test_time_based_partition_params_invariants(
    schedule_type: ScheduleType,
    start: datetime,
    execution_day: Optional[int],
    end: Optional[datetime],
    error_message_regex: str,
):
    with pytest.raises(CheckError, match=error_message_regex):
        TimeBasedPartitionParams(
            schedule_type=schedule_type,
            start=start,
            execution_day=execution_day,
            execution_time=None,
            end=end,
            fmt=None,
            inclusive=None,
            timezone=None,
            offset=None,
        )


@pytest.mark.parametrize(
    argnames=[
        "schedule_type",
        "start",
        "execution_day",
        "execution_time",
        "end",
        "fmt",
        "inclusive",
        "timezone",
        "offset",
        "expected_partitions",
    ],
    ids=[
        "daily partitions, not inclusive",
        "daily partitions, inclusive",
        "daily partitions, different start/end year",
        "daily partitions, leap year",
        "daily partitions, not leap year",
        "monthly partitions",
        "monthly partitions, different start/end year",
        "monthly partitions, start/end not at least a month apart",
        "weekly partitions",
        "hourly partitions, Spring DST",
        "hourly partitions, Spring DST with timezone",
        "hourly partitions, Fall DST",
        "hourly partitions, Fall DST with timezone",
    ],
    argvalues=[
        (
            ScheduleType.DAILY,
            datetime(year=2020, month=1, day=1),
            None,
            None,
            datetime(year=2020, month=1, day=6),
            None,
            False,
            None,
            None,
            ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04", "2020-01-05"],
        ),
        (
            ScheduleType.DAILY,
            datetime(year=2020, month=1, day=1),
            None,
            None,
            datetime(year=2020, month=1, day=6, hour=1),
            None,
            True,
            None,
            None,
            ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04", "2020-01-05", "2020-01-06"],
        ),
        (
            ScheduleType.DAILY,
            datetime(year=2020, month=12, day=29),
            None,
            None,
            datetime(year=2021, month=1, day=3),
            None,
            None,
            None,
            None,
            ["2020-12-29", "2020-12-30", "2020-12-31", "2021-01-01", "2021-01-02"],
        ),
        (
            ScheduleType.DAILY,
            datetime(year=2020, month=2, day=28),
            None,
            None,
            datetime(year=2020, month=3, day=3),
            None,
            None,
            None,
            None,
            ["2020-02-28", "2020-02-29", "2020-03-01", "2020-03-02"],
        ),
        (
            ScheduleType.DAILY,
            datetime(year=2019, month=2, day=28),
            None,
            None,
            datetime(year=2019, month=3, day=3),
            None,
            None,
            None,
            None,
            ["2019-02-28", "2019-03-01", "2019-03-02"],
        ),
        (
            ScheduleType.MONTHLY,
            datetime(year=2020, month=1, day=1),
            None,
            None,
            datetime(year=2020, month=3, day=6),
            None,
            None,
            None,
            None,
            ["2020-01-01", "2020-02-01"],
        ),
        (
            ScheduleType.MONTHLY,
            datetime(year=2020, month=12, day=1),
            None,
            None,
            datetime(year=2021, month=2, day=6),
            None,
            None,
            None,
            None,
            ["2020-12-01", "2021-01-01"],
        ),
        (
            ScheduleType.MONTHLY,
            datetime(year=2020, month=2, day=12),
            None,
            None,
            datetime(year=2020, month=3, day=11),
            None,
            None,
            None,
            None,
            [],
        ),
        (
            ScheduleType.WEEKLY,
            datetime(year=2020, month=1, day=1),
            None,
            None,
            datetime(year=2020, month=1, day=27),
            None,
            None,
            None,
            None,
            ["2020-01-01", "2020-01-08", "2020-01-15"],
        ),
        (
            ScheduleType.HOURLY,
            datetime(year=2019, month=3, day=10, hour=1),
            None,
            None,
            datetime(year=2019, month=3, day=10, hour=4),
            DEFAULT_HOURLY_FORMAT_WITH_TIMEZONE,
            True,
            "UTC",
            None,
            [
                "2019-03-10-01:00+0000",
                "2019-03-10-02:00+0000",
                "2019-03-10-03:00+0000",
                "2019-03-10-04:00+0000",
            ],
        ),
        (
            ScheduleType.HOURLY,
            datetime(year=2019, month=3, day=10, hour=1),
            None,
            None,
            datetime(year=2019, month=3, day=10, hour=4),
            DEFAULT_HOURLY_FORMAT_WITH_TIMEZONE,
            True,
            "US/Central",
            None,
            ["2019-03-10-01:00-0600", "2019-03-10-03:00-0500", "2019-03-10-04:00-0500"],
        ),
        (
            ScheduleType.HOURLY,
            datetime(year=2019, month=11, day=3, hour=0),
            None,
            None,
            datetime(year=2019, month=11, day=3, hour=3),
            DEFAULT_HOURLY_FORMAT_WITH_TIMEZONE,
            True,
            "UTC",
            None,
            [
                "2019-11-03-00:00+0000",
                "2019-11-03-01:00+0000",
                "2019-11-03-02:00+0000",
                "2019-11-03-03:00+0000",
            ],
        ),
        (
            ScheduleType.HOURLY,
            datetime(year=2019, month=11, day=3, hour=0),
            None,
            None,
            datetime(year=2019, month=11, day=3, hour=3),
            DEFAULT_HOURLY_FORMAT_WITH_TIMEZONE,
            True,
            "US/Central",
            None,
            [
                "2019-11-03-00:00-0500",
                "2019-11-03-01:00-0500",
                "2019-11-03-01:00-0600",
                "2019-11-03-02:00-0600",
                "2019-11-03-03:00-0600",
            ],
        ),
    ],
)
def test_time_based_partition_params(
    schedule_type: ScheduleType,
    start: datetime,
    execution_day: Optional[int],
    execution_time: Optional[time],
    end: Optional[datetime],
    fmt: Optional[str],
    inclusive: Optional[bool],
    timezone: Optional[str],
    offset: Optional[int],
    expected_partitions: List[str],
):
    partition_params = TimeBasedPartitionParams(
        schedule_type=schedule_type,
        start=start,
        execution_day=execution_day,
        execution_time=execution_time,
        end=end,
        fmt=fmt,
        inclusive=inclusive,
        timezone=timezone,
        offset=offset,
    )

    generated_partitions = partition_params.get_partitions(current_time=None)

    assert all(
        isinstance(generated_partition, Partition) for generated_partition in generated_partitions
    )
    assert len(generated_partitions) == len(expected_partitions)
    assert all(
        generated_partition.name == expected_partition_name
        for generated_partition, expected_partition_name in zip(
            generated_partitions, expected_partitions
        )
    )


@pytest.mark.parametrize(
    argnames=["partition_fn"],
    argvalues=[
        (lambda _current_time: [Partition("a_partition")],),
        (lambda _current_time: [Partition(x) for x in range(10)],),
    ],
)
def test_dynamic_partitions(partition_fn: Callable[[Optional[datetime]], List[Partition]]):
    partition_params = DynamicPartitionParams(partition_fn)

    assert partition_params.get_partitions(current_time=None) == partition_fn(None)
