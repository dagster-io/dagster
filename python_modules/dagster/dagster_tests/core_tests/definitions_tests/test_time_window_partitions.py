from datetime import datetime

import pendulum
from dagster.core.definitions.time_window_partitions import (
    TimeWindow,
    daily_partitioned_config,
    monthly_partitioned_config,
)

DATE_FORMAT = "%Y-%m-%d"


def time_window(start: str, end: str) -> TimeWindow:
    return TimeWindow(pendulum.parse(start), pendulum.parse(end))


def test_daily_partitions():
    @daily_partitioned_config(start_date="2021-05-05")
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
    ]


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


def test_monthly_partitions():
    @monthly_partitioned_config(start_date="2021-05-01")
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
    ]


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
