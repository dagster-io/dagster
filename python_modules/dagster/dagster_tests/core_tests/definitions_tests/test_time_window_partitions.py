from datetime import datetime
from typing import cast

import pendulum
import pytest

from dagster import (
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
    MonthlyPartitionsDefinition,
    PartitionKeyRange,
    WeeklyPartitionsDefinition,
    daily_partitioned_config,
    hourly_partitioned_config,
    monthly_partitioned_config,
    weekly_partitioned_config,
)
from dagster._utils.partitions import DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE
from dagster._core.definitions.time_window_partitions import TimeWindow

DATE_FORMAT = "%Y-%m-%d"


def time_window(start: str, end: str) -> TimeWindow:
    return TimeWindow(cast(datetime, pendulum.parse(start)), cast(datetime, pendulum.parse(end)))


def test_daily_partitions():
    @daily_partitioned_config(start_date="2021-05-05")
    def my_partitioned_config(_start, _end):
        return {}

    partitions_def = my_partitioned_config.partitions_def
    assert partitions_def == DailyPartitionsDefinition(start_date="2021-05-05")

    assert [
        partition.value
        for partition in partitions_def.get_partitions(datetime.strptime("2021-05-07", DATE_FORMAT))
    ] == [
        time_window("2021-05-05", "2021-05-06"),
        time_window("2021-05-06", "2021-05-07"),
    ]

    assert partitions_def.time_window_for_partition_key("2021-05-08") == time_window(
        "2021-05-08", "2021-05-09"
    )


def test_daily_partitions_with_end_offset():
    @daily_partitioned_config(start_date="2021-05-05", end_offset=2)
    def my_partitioned_config(_start, _end):
        return {}

    assert [
        partition.value
        for partition in my_partitioned_config.partitions_def.get_partitions(
            datetime.strptime("2021-05-07", DATE_FORMAT)
        )
    ] == [
        time_window("2021-05-05", "2021-05-06"),
        time_window("2021-05-06", "2021-05-07"),
        time_window("2021-05-07", "2021-05-08"),
        time_window("2021-05-08", "2021-05-09"),
    ]


def test_daily_partitions_with_negative_end_offset():
    @daily_partitioned_config(start_date="2021-05-01", end_offset=-2)
    def my_partitioned_config(_start, _end):
        return {}

    assert [
        partition.value
        for partition in my_partitioned_config.partitions_def.get_partitions(
            datetime.strptime("2021-05-07", DATE_FORMAT)
        )
    ] == [
        time_window("2021-05-01", "2021-05-02"),
        time_window("2021-05-02", "2021-05-03"),
        time_window("2021-05-03", "2021-05-04"),
        time_window("2021-05-04", "2021-05-05"),
    ]


def test_daily_partitions_with_time_offset():
    @daily_partitioned_config(start_date="2021-05-05", minute_offset=15)
    def my_partitioned_config(_start, _end):
        return {}

    partitions_def = my_partitioned_config.partitions_def
    assert partitions_def == DailyPartitionsDefinition(start_date="2021-05-05", minute_offset=15)

    partitions = partitions_def.get_partitions(datetime.strptime("2021-05-07", DATE_FORMAT))

    assert [partition.value for partition in partitions] == [
        time_window("2021-05-05T00:15:00", "2021-05-06T00:15:00"),
    ]

    assert [partition.name for partition in partitions] == [
        "2021-05-05",
    ]

    assert partitions_def.time_window_for_partition_key("2021-05-08") == time_window(
        "2021-05-08T00:15:00", "2021-05-09T00:15:00"
    )


def test_monthly_partitions():
    @monthly_partitioned_config(start_date="2021-05-01")
    def my_partitioned_config(_start, _end):
        return {}

    partitions_def = my_partitioned_config.partitions_def
    assert partitions_def == MonthlyPartitionsDefinition(start_date="2021-05-01")

    assert [
        partition.value
        for partition in partitions_def.get_partitions(datetime.strptime("2021-07-03", DATE_FORMAT))
    ] == [
        time_window("2021-05-01", "2021-06-01"),
        time_window("2021-06-01", "2021-07-01"),
    ]

    assert partitions_def.time_window_for_partition_key("2021-05-01") == time_window(
        "2021-05-01", "2021-06-01"
    )


def test_monthly_partitions_with_end_offset():
    @monthly_partitioned_config(start_date="2021-05-01", end_offset=2)
    def my_partitioned_config(_start, _end):
        return {}

    assert [
        partition.value
        for partition in my_partitioned_config.partitions_def.get_partitions(
            datetime.strptime("2021-07-03", DATE_FORMAT)
        )
    ] == [
        time_window("2021-05-01", "2021-06-01"),
        time_window("2021-06-01", "2021-07-01"),
        time_window("2021-07-01", "2021-08-01"),
        time_window("2021-08-01", "2021-09-01"),
    ]


def test_monthly_partitions_with_time_offset():
    @monthly_partitioned_config(
        start_date="2021-05-01", minute_offset=15, hour_offset=3, day_offset=12
    )
    def my_partitioned_config(_start, _end):
        return {}

    partitions_def = my_partitioned_config.partitions_def
    assert partitions_def == MonthlyPartitionsDefinition(
        start_date="2021-05-01", minute_offset=15, hour_offset=3, day_offset=12
    )

    partitions = partitions_def.get_partitions(datetime.strptime("2021-07-13", DATE_FORMAT))

    assert [partition.value for partition in partitions] == [
        time_window("2021-05-12T03:15:00", "2021-06-12T03:15:00"),
        time_window("2021-06-12T03:15:00", "2021-07-12T03:15:00"),
    ]

    assert [partition.name for partition in partitions] == [
        "2021-05-12",
        "2021-06-12",
    ]

    assert partitions_def.time_window_for_partition_key("2021-05-01") == time_window(
        "2021-05-12T03:15:00", "2021-06-12T03:15:00"
    )


def test_hourly_partitions():
    @hourly_partitioned_config(start_date="2021-05-05-01:00")
    def my_partitioned_config(_start, _end):
        return {}

    partitions_def = my_partitioned_config.partitions_def
    assert partitions_def == HourlyPartitionsDefinition(start_date="2021-05-05-01:00")

    partitions = partitions_def.get_partitions(
        datetime.strptime("2021-05-05-03:00", DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE)
    )

    assert [partition.value for partition in partitions] == [
        time_window("2021-05-05T01:00:00", "2021-05-05T02:00:00"),
        time_window("2021-05-05T02:00:00", "2021-05-05T03:00:00"),
    ]

    assert [partition.name for partition in partitions] == [
        "2021-05-05-01:00",
        "2021-05-05-02:00",
    ]

    assert partitions_def.time_window_for_partition_key("2021-05-05-01:00") == time_window(
        "2021-05-05T01:00:00", "2021-05-05T02:00:00"
    )


def test_hourly_partitions_with_time_offset():
    @hourly_partitioned_config(start_date="2021-05-05-01:00", minute_offset=15)
    def my_partitioned_config(_start, _end):
        return {}

    partitions_def = my_partitioned_config.partitions_def
    assert partitions_def == HourlyPartitionsDefinition(
        start_date="2021-05-05-01:00", minute_offset=15
    )

    partitions = partitions_def.get_partitions(
        datetime.strptime("2021-05-05-03:30", DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE)
    )

    assert [partition.value for partition in partitions] == [
        time_window("2021-05-05T01:15:00", "2021-05-05T02:15:00"),
        time_window("2021-05-05T02:15:00", "2021-05-05T03:15:00"),
    ]

    assert [partition.name for partition in partitions] == [
        "2021-05-05-01:15",
        "2021-05-05-02:15",
    ]

    assert partitions_def.time_window_for_partition_key("2021-05-05-01:00") == time_window(
        "2021-05-05T01:15:00", "2021-05-05T02:15:00"
    )


def test_weekly_partitions():
    @weekly_partitioned_config(start_date="2021-05-01")
    def my_partitioned_config(_start, _end):
        return {}

    partitions_def = my_partitioned_config.partitions_def
    assert partitions_def == WeeklyPartitionsDefinition(start_date="2021-05-01")

    assert [
        partition.value
        for partition in partitions_def.get_partitions(datetime.strptime("2021-05-18", DATE_FORMAT))
    ] == [
        time_window("2021-05-02", "2021-05-09"),
        time_window("2021-05-09", "2021-05-16"),
    ]

    assert partitions_def.time_window_for_partition_key("2021-05-01") == time_window(
        "2021-05-02", "2021-05-09"
    )


def test_weekly_partitions_with_time_offset():
    @weekly_partitioned_config(
        start_date="2021-05-01", minute_offset=15, hour_offset=4, day_offset=3
    )
    def my_partitioned_config(_start, _end):
        return {}

    partitions_def = my_partitioned_config.partitions_def
    assert partitions_def == WeeklyPartitionsDefinition(
        start_date="2021-05-01", minute_offset=15, hour_offset=4, day_offset=3
    )

    partitions = partitions_def.get_partitions(datetime.strptime("2021-05-20", DATE_FORMAT))

    assert [partition.value for partition in partitions] == [
        time_window("2021-05-05T04:15:00", "2021-05-12T04:15:00"),
        time_window("2021-05-12T04:15:00", "2021-05-19T04:15:00"),
    ]

    assert [partition.name for partition in partitions] == [
        "2021-05-05",
        "2021-05-12",
    ]

    assert partitions_def.time_window_for_partition_key("2021-05-01") == time_window(
        "2021-05-05T04:15:00", "2021-05-12T04:15:00"
    )


@pytest.mark.parametrize(
    "partitions_def, range_start, range_end, partition_keys",
    [
        [
            DailyPartitionsDefinition(start_date="2021-05-01"),
            "2021-05-01",
            "2021-05-01",
            ["2021-05-01"],
        ],
        [
            DailyPartitionsDefinition(start_date="2021-05-01"),
            "2021-05-02",
            "2021-05-05",
            ["2021-05-02", "2021-05-03", "2021-05-04", "2021-05-05"],
        ],
    ],
)
def test_get_partition_keys_in_range(partitions_def, range_start, range_end, partition_keys):
    assert (
        partitions_def.get_partition_keys_in_range(PartitionKeyRange(range_start, range_end))
        == partition_keys
    )
