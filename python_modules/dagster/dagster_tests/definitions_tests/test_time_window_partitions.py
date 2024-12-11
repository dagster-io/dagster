import pickle
import random
from datetime import datetime, timedelta
from typing import Optional, Sequence, cast

import pytest
from dagster import (
    DagsterInvalidDefinitionError,
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
    MonthlyPartitionsDefinition,
    PartitionKeyRange,
    TimeWindowPartitionsDefinition,
    WeeklyPartitionsDefinition,
    daily_partitioned_config,
    hourly_partitioned_config,
    monthly_partitioned_config,
    weekly_partitioned_config,
)
from dagster._check import CheckError
from dagster._core.definitions.time_window_partitions import (
    PersistedTimeWindow,
    ScheduleType,
    TimeWindow,
    TimeWindowPartitionsSubset,
    dst_safe_strptime,
)
from dagster._core.definitions.timestamp import TimestampWithTimezone
from dagster._core.test_utils import freeze_time
from dagster._record import copy
from dagster._serdes import deserialize_value, serialize_value
from dagster._time import create_datetime, parse_time_string
from dagster._utils.partitions import DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE

DATE_FORMAT = "%Y-%m-%d"


def time_window(start: str, end: str) -> TimeWindow:
    return TimeWindow(
        cast(datetime, parse_time_string(start)),
        cast(datetime, parse_time_string(end)),
    )


def persisted_time_window(start: str, end: str) -> PersistedTimeWindow:
    return PersistedTimeWindow(
        TimestampWithTimezone(parse_time_string(start).timestamp(), "UTC"),
        TimestampWithTimezone(parse_time_string(end).timestamp(), "UTC"),
    )


def test_daily_partitions():
    @daily_partitioned_config(start_date="2021-05-05")
    def my_partitioned_config(_start, _end):
        return {}

    partitions_def = my_partitioned_config.partitions_def
    assert partitions_def == DailyPartitionsDefinition(start_date="2021-05-05")
    assert copy(partitions_def) == DailyPartitionsDefinition(start_date="2021-05-05")

    assert partitions_def.get_next_partition_key("2021-05-05") == "2021-05-06"
    assert partitions_def.get_last_partition_key(parse_time_string("2021-05-06")) == "2021-05-05"
    assert (
        partitions_def.get_last_partition_key(
            parse_time_string("2021-05-06") + timedelta(minutes=1)
        )
        == "2021-05-05"
    )
    assert (
        partitions_def.get_last_partition_key(
            parse_time_string("2021-05-07") - timedelta(minutes=1)
        )
        == "2021-05-05"
    )
    assert partitions_def.schedule_type == ScheduleType.DAILY

    assert [
        partitions_def.time_window_for_partition_key(key)
        for key in partitions_def.get_partition_keys(datetime.strptime("2021-05-07", DATE_FORMAT))
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

    partitions_def = my_partitioned_config.partitions_def
    assert [
        partitions_def.time_window_for_partition_key(key)
        for key in partitions_def.get_partition_keys(datetime.strptime("2021-05-07", DATE_FORMAT))
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

    partitions_def = my_partitioned_config.partitions_def
    assert [
        partitions_def.time_window_for_partition_key(key)
        for key in partitions_def.get_partition_keys(datetime.strptime("2021-05-07", DATE_FORMAT))
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

    partition_keys = partitions_def.get_partition_keys(datetime.strptime("2021-05-07", DATE_FORMAT))
    assert partition_keys == ["2021-05-05"]

    assert [partitions_def.time_window_for_partition_key(key) for key in partition_keys] == [
        time_window("2021-05-05T00:15:00", "2021-05-06T00:15:00"),
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
    assert copy(partitions_def) == MonthlyPartitionsDefinition(start_date="2021-05-01")

    assert [
        partitions_def.time_window_for_partition_key(key)
        for key in partitions_def.get_partition_keys(datetime.strptime("2021-07-03", DATE_FORMAT))
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

    partitions_def = my_partitioned_config.partitions_def
    assert [
        partitions_def.time_window_for_partition_key(key)
        for key in partitions_def.get_partition_keys(datetime.strptime("2021-07-03", DATE_FORMAT))
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
    assert partitions_def.minute_offset == 15
    assert partitions_def.hour_offset == 3
    assert partitions_def.day_offset == 12
    assert partitions_def == MonthlyPartitionsDefinition(
        start_date="2021-05-01", minute_offset=15, hour_offset=3, day_offset=12
    )

    partition_keys = partitions_def.get_partition_keys(datetime.strptime("2021-07-13", DATE_FORMAT))
    assert partition_keys == [
        "2021-05-12",
        "2021-06-12",
    ]

    assert [partitions_def.time_window_for_partition_key(key) for key in partition_keys] == [
        time_window("2021-05-12T03:15:00", "2021-06-12T03:15:00"),
        time_window("2021-06-12T03:15:00", "2021-07-12T03:15:00"),
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
    assert copy(partitions_def) == HourlyPartitionsDefinition(start_date="2021-05-05-01:00")

    partition_keys = partitions_def.get_partition_keys(
        datetime.strptime("2021-05-05-03:00", DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE)
    )
    assert partition_keys == [
        "2021-05-05-01:00",
        "2021-05-05-02:00",
    ]

    assert [partitions_def.time_window_for_partition_key(key) for key in partition_keys] == [
        time_window("2021-05-05T01:00:00", "2021-05-05T02:00:00"),
        time_window("2021-05-05T02:00:00", "2021-05-05T03:00:00"),
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

    partition_keys = partitions_def.get_partition_keys(
        datetime.strptime("2021-05-05-03:30", DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE)
    )
    assert partition_keys == [
        "2021-05-05-01:15",
        "2021-05-05-02:15",
    ]

    assert [partitions_def.time_window_for_partition_key(key) for key in partition_keys] == [
        time_window("2021-05-05T01:15:00", "2021-05-05T02:15:00"),
        time_window("2021-05-05T02:15:00", "2021-05-05T03:15:00"),
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
    assert copy(partitions_def) == WeeklyPartitionsDefinition(start_date="2021-05-01")

    partitions_def = my_partitioned_config.partitions_def
    assert [
        partitions_def.time_window_for_partition_key(key)
        for key in partitions_def.get_partition_keys(datetime.strptime("2021-05-18", DATE_FORMAT))
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

    partition_keys = partitions_def.get_partition_keys(datetime.strptime("2021-05-20", DATE_FORMAT))
    assert partition_keys == [
        "2021-05-05",
        "2021-05-12",
    ]

    assert [partitions_def.time_window_for_partition_key(key) for key in partition_keys] == [
        time_window("2021-05-05T04:15:00", "2021-05-12T04:15:00"),
        time_window("2021-05-12T04:15:00", "2021-05-19T04:15:00"),
    ]

    assert partitions_def.time_window_for_partition_key("2021-05-01") == time_window(
        "2021-05-05T04:15:00", "2021-05-12T04:15:00"
    )


def test_partitioned_config_invalid_offsets():
    with pytest.raises(DagsterInvalidDefinitionError, match="Found invalid cron schedule"):

        @weekly_partitioned_config(start_date=datetime(year=2021, month=1, day=1), day_offset=8)
        def my_weekly_partitioned_config(_start, _end):
            return {}

    with pytest.raises(DagsterInvalidDefinitionError, match="Found invalid cron schedule"):

        @monthly_partitioned_config(start_date=datetime(year=2021, month=1, day=1), day_offset=32)
        def my_monthly_partitioned_config(_start, _end):
            return {}


def assert_expected_partition_keys(
    generated_partition_keys: Sequence[str], expected_partition_keys: Sequence[str]
):
    assert all(isinstance(generated_key, str) for generated_key in generated_partition_keys)
    assert len(generated_partition_keys) == len(expected_partition_keys)
    for generated_key, expected_key in zip(generated_partition_keys, expected_partition_keys):
        assert generated_key == expected_key


@pytest.mark.parametrize(
    argnames=[
        "start",
        "partition_days_offset",
        "current_time",
        "expected_partition_keys",
        "timezone",
    ],
    ids=[
        "partition days offset == 0",
        "partition days offset == 1",
        "partition days offset > 1",
        "partition days offset < 1",
        "different start/end year",
        "leap year",
        "not leap year",
    ],
    argvalues=[
        (
            datetime(year=2021, month=1, day=1),
            0,
            create_datetime(2021, 1, 6, 1, 20),
            ["2021-01-01", "2021-01-02", "2021-01-03", "2021-01-04", "2021-01-05"],
            None,
        ),
        (
            datetime(year=2021, month=1, day=1),
            1,
            create_datetime(2021, 1, 6, 1, 20),
            [
                "2021-01-01",
                "2021-01-02",
                "2021-01-03",
                "2021-01-04",
                "2021-01-05",
                "2021-01-06",
            ],
            None,
        ),
        (
            datetime(year=2021, month=1, day=1),
            2,
            create_datetime(2021, 1, 6, 1, 20),
            [
                "2021-01-01",
                "2021-01-02",
                "2021-01-03",
                "2021-01-04",
                "2021-01-05",
                "2021-01-06",
                "2021-01-07",
            ],
            None,
        ),
        (
            datetime(year=2021, month=1, day=1),
            -2,
            create_datetime(2021, 1, 8, 1, 20),
            [
                "2021-01-01",
                "2021-01-02",
                "2021-01-03",
                "2021-01-04",
                "2021-01-05",
            ],
            None,
        ),
        (
            datetime(year=2020, month=12, day=29),
            0,
            create_datetime(2021, 1, 3, 1, 20),
            ["2020-12-29", "2020-12-30", "2020-12-31", "2021-01-01", "2021-01-02"],
            None,
        ),
        (
            datetime(year=2020, month=2, day=28),
            0,
            create_datetime(2020, 3, 3, 1, 20),
            ["2020-02-28", "2020-02-29", "2020-03-01", "2020-03-02"],
            None,
        ),
        (
            datetime(year=2021, month=2, day=28),
            0,
            create_datetime(2021, 3, 3, 1, 20),
            ["2021-02-28", "2021-03-01", "2021-03-02"],
            None,
        ),
    ],
)
def test_time_partitions_daily_partitions(
    start: datetime,
    partition_days_offset: int,
    current_time: Optional[datetime],
    expected_partition_keys: Sequence[str],
    timezone: Optional[str],
):
    partitions_def = DailyPartitionsDefinition(
        start_date=start, end_offset=partition_days_offset, timezone=timezone
    )

    assert_expected_partition_keys(
        partitions_def.get_partition_keys(current_time=current_time),
        expected_partition_keys,
    )


@pytest.mark.parametrize(
    argnames=[
        "start",
        "partition_months_offset",
        "current_time",
        "expected_partition_keys",
    ],
    ids=[
        "partition months offset == 0",
        "partition months offset == 1",
        "partition months offset > 1",
        "partition months offset < 1",
        "execution day of month not within start/end range",
    ],
    argvalues=[
        (
            datetime(year=2021, month=1, day=1),
            0,
            create_datetime(2021, 3, 1, 1, 20),
            ["2021-01-01", "2021-02-01"],
        ),
        (
            datetime(year=2021, month=1, day=1),
            1,
            create_datetime(2021, 3, 1, 1, 20),
            ["2021-01-01", "2021-02-01", "2021-03-01"],
        ),
        (
            datetime(year=2021, month=1, day=1),
            2,
            create_datetime(2021, 3, 1, 1, 20),
            ["2021-01-01", "2021-02-01", "2021-03-01", "2021-04-01"],
        ),
        (
            datetime(year=2021, month=1, day=1),
            -1,
            create_datetime(2021, 3, 27),
            ["2021-01-01"],
        ),
        (
            datetime(year=2021, month=1, day=3),
            0,
            create_datetime(2021, 1, 31),
            [],
        ),
    ],
)
def test_time_partitions_monthly_partitions(
    start: datetime,
    partition_months_offset: int,
    current_time,
    expected_partition_keys: Sequence[str],
):
    partitions_def = MonthlyPartitionsDefinition(
        start_date=start, end_offset=partition_months_offset
    )

    assert_expected_partition_keys(
        partitions_def.get_partition_keys(current_time=current_time),
        expected_partition_keys,
    )


@pytest.mark.parametrize(
    argnames=[
        "start",
        "partition_weeks_offset",
        "current_time",
        "expected_partition_keys",
    ],
    ids=[
        "partition weeks offset == 0",
        "partition weeks offset == 1",
        "partition weeks offset > 1",
        "partition weeks offset < 1",
        "execution day of week not within start/end range",
    ],
    argvalues=[
        (
            datetime(year=2021, month=1, day=1),
            0,
            create_datetime(2021, 1, 31, 1, 20),
            ["2021-01-03", "2021-01-10", "2021-01-17", "2021-01-24"],
        ),
        (
            datetime(year=2021, month=1, day=1),
            1,
            create_datetime(2021, 1, 31, 1, 20),
            ["2021-01-03", "2021-01-10", "2021-01-17", "2021-01-24", "2021-01-31"],
        ),
        (
            datetime(year=2021, month=1, day=1),
            2,
            create_datetime(2021, 1, 31, 1, 20),
            [
                "2021-01-03",
                "2021-01-10",
                "2021-01-17",
                "2021-01-24",
                "2021-01-31",
                "2021-02-07",
            ],
        ),
        (
            datetime(year=2021, month=1, day=1),
            -2,
            create_datetime(2021, 1, 24, 1, 20),
            ["2021-01-03"],
        ),
        (
            datetime(year=2021, month=1, day=4),
            0,
            create_datetime(2021, 1, 9),
            [],
        ),
    ],
)
def test_time_partitions_weekly_partitions(
    start: datetime,
    partition_weeks_offset: int,
    current_time,
    expected_partition_keys: Sequence[str],
):
    partitions_def = WeeklyPartitionsDefinition(start_date=start, end_offset=partition_weeks_offset)

    assert_expected_partition_keys(
        partitions_def.get_partition_keys(current_time=current_time),
        expected_partition_keys,
    )


@pytest.mark.parametrize(
    argnames=[
        "start",
        "timezone",
        "partition_hours_offset",
        "current_time",
        "expected_partition_keys",
    ],
    ids=[
        "partition hours offset == 0",
        "partition hours offset == 1",
        "partition hours offset > 1",
        "partition hours offset < 1",
        "execution hour not within start/end range",
        "Spring DST",
        "Spring DST with timezone",
        "Fall DST",
        "Fall DST with timezone",
    ],
    argvalues=[
        (
            datetime(year=2021, month=1, day=1, hour=0),
            None,
            0,
            create_datetime(2021, 1, 1, 4, 1),
            [
                "2021-01-01-00:00",
                "2021-01-01-01:00",
                "2021-01-01-02:00",
                "2021-01-01-03:00",
            ],
        ),
        (
            datetime(year=2021, month=1, day=1, hour=0),
            None,
            1,
            create_datetime(2021, 1, 1, 4, 1),
            [
                "2021-01-01-00:00",
                "2021-01-01-01:00",
                "2021-01-01-02:00",
                "2021-01-01-03:00",
                "2021-01-01-04:00",
            ],
        ),
        (
            datetime(year=2021, month=1, day=1, hour=0),
            None,
            2,
            create_datetime(2021, 1, 1, 4, 1),
            [
                "2021-01-01-00:00",
                "2021-01-01-01:00",
                "2021-01-01-02:00",
                "2021-01-01-03:00",
                "2021-01-01-04:00",
                "2021-01-01-05:00",
            ],
        ),
        (
            datetime(year=2021, month=1, day=1, hour=0),
            None,
            -1,
            create_datetime(2021, 1, 1, 3, 30),
            ["2021-01-01-00:00", "2021-01-01-01:00"],
        ),
        (
            datetime(year=2021, month=1, day=1, hour=0, minute=2),
            None,
            0,
            create_datetime(2021, 1, 1, 0, 59),
            [],
        ),
        (
            datetime(year=2021, month=3, day=14, hour=1),
            None,
            0,
            create_datetime(2021, 3, 14, 4, 1),
            [
                "2021-03-14-01:00",
                "2021-03-14-02:00",
                "2021-03-14-03:00",
            ],
        ),
        (
            datetime(year=2021, month=3, day=14, hour=1),
            "US/Central",
            0,
            create_datetime(2021, 3, 14, 4, 1, tz="US/Central"),
            ["2021-03-14-01:00", "2021-03-14-03:00"],
        ),
        (
            datetime(year=2021, month=11, day=7, hour=0),
            None,
            0,
            create_datetime(2021, 11, 7, 4, 1),
            [
                "2021-11-07-00:00",
                "2021-11-07-01:00",
                "2021-11-07-02:00",
                "2021-11-07-03:00",
            ],
        ),
        (
            datetime(year=2021, month=11, day=7, hour=0),
            "US/Central",
            0,
            create_datetime(2021, 11, 7, 4, 1, tz="US/Central"),
            [
                "2021-11-07-00:00",
                "2021-11-07-01:00",
                "2021-11-07-01:00-0600",
                "2021-11-07-02:00",
                "2021-11-07-03:00",
            ],
        ),
    ],
)
def test_time_partitions_hourly_partitions(
    start: datetime,
    timezone: Optional[str],
    partition_hours_offset: int,
    current_time,
    expected_partition_keys: Sequence[str],
):
    partitions_def = HourlyPartitionsDefinition(
        start_date=start, end_offset=partition_hours_offset, timezone=timezone
    )

    assert_expected_partition_keys(
        partitions_def.get_partition_keys(current_time=current_time),
        expected_partition_keys,
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


def test_invalid_get_partition_keys_in_range():
    partitions_def = DailyPartitionsDefinition(start_date="2020-01-01", end_date="2020-01-05")
    with pytest.raises(CheckError, match="before the partitions definition start time"):
        partitions_def.get_partition_keys_in_range(PartitionKeyRange("2019-12-12", "2020-01-01"))

    with pytest.raises(CheckError, match="after the partitions definition end time"):
        partitions_def.get_partition_keys_in_range(PartitionKeyRange("2020-01-01", "2020-01-06"))

    assert partitions_def.get_partition_keys_in_range(
        PartitionKeyRange("2020-01-01", "2020-01-04")
    ) == ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04"]


def test_twice_daily_partitions():
    partitions_def = TimeWindowPartitionsDefinition(
        start=parse_time_string("2021-05-05"),
        cron_schedule="0 0,11 * * *",
        fmt=DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE,
    )

    assert [
        partitions_def.time_window_for_partition_key(key)
        for key in partitions_def.get_partition_keys(datetime.strptime("2021-05-07", DATE_FORMAT))
    ] == [
        time_window("2021-05-05T00:00:00", "2021-05-05T11:00:00"),
        time_window("2021-05-05T11:00:00", "2021-05-06T00:00:00"),
        time_window("2021-05-06T00:00:00", "2021-05-06T11:00:00"),
        time_window("2021-05-06T11:00:00", "2021-05-07T00:00:00"),
    ]

    assert partitions_def.time_window_for_partition_key("2021-05-08-00:00") == time_window(
        "2021-05-08T00:00:00", "2021-05-08T11:00:00"
    )
    assert partitions_def.time_window_for_partition_key("2021-05-08-11:00") == time_window(
        "2021-05-08T11:00:00", "2021-05-09T00:00:00"
    )


def test_start_not_aligned():
    partitions_def = TimeWindowPartitionsDefinition(
        start=parse_time_string("2021-05-05"),
        cron_schedule="0 7 * * *",
        fmt=DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE,
    )

    assert [
        partitions_def.time_window_for_partition_key(key)
        for key in partitions_def.get_partition_keys(datetime.strptime("2021-05-08", DATE_FORMAT))
    ] == [
        time_window("2021-05-05T07:00:00", "2021-05-06T07:00:00"),
        time_window("2021-05-06T07:00:00", "2021-05-07T07:00:00"),
    ]


@pytest.mark.parametrize(
    "case_str",
    [
        "+",
        "+-",
        "+--",
        "-+",
        "-+-",
        "-++",
        "-++-",
        "-+++-",
        "--++",
        "-+-+-",
        "--+++---+++--",
    ],
)
def test_partition_subset_get_partition_keys_not_in_subset(case_str: str):
    partitions_def = DailyPartitionsDefinition(start_date="2015-01-01")
    full_set_keys = partitions_def.get_partition_keys(
        current_time=datetime(year=2015, month=1, day=30)
    )[: len(case_str)]
    subset_keys = []
    expected_keys_not_in_subset = []
    for i, c in enumerate(case_str):
        if c == "+":
            subset_keys.append(full_set_keys[i])
        else:
            expected_keys_not_in_subset.append(full_set_keys[i])

    subset = cast(
        TimeWindowPartitionsSubset,
        TimeWindowPartitionsSubset.create_empty_subset(partitions_def).with_partition_keys(
            subset_keys
        ),
    )
    for partition_key in subset_keys:
        assert partition_key in subset
    assert (
        subset.get_partition_keys_not_in_subset(
            partitions_def=partitions_def,
            current_time=partitions_def.end_time_for_partition_key(full_set_keys[-1]),
        )
        == expected_keys_not_in_subset
    )
    assert (
        cast(
            TimeWindowPartitionsSubset, partitions_def.deserialize_subset(subset.serialize())
        ).included_time_windows
        == subset.included_time_windows
    )

    expected_range_count = case_str.count("-+") + (1 if case_str[0] == "+" else 0)
    assert len(subset.included_time_windows) == expected_range_count, case_str
    assert len(subset) == case_str.count("+")


def test_time_partitions_subset_identical_serialization():
    # serialized subsets should be equal if the original subsets are equal
    partitions_def = DailyPartitionsDefinition(start_date="2015-01-01")
    partition_keys = [
        *[f"2015-02-{i:02d}" for i in range(1, 20)],
        *[f"2016-03-{i:02d}" for i in range(1, 15)],
        *[f"2017-04-{i:02d}" for i in range(1, 10)],
        *[f"2018-05-{i:02d}" for i in range(1, 5)],
        *[f"2018-06-{i:02d}" for i in range(1, 10)],
        *[f"2019-07-{i:02d}" for i in range(1, 15)],
        *[f"2020-08-{i:02d}" for i in range(1, 20)],
    ]
    serialized1 = partitions_def.subset_with_partition_keys(partition_keys).serialize()
    random.shuffle(partition_keys)
    serialized2 = partitions_def.subset_with_partition_keys(partition_keys).serialize()
    assert serialized1 == serialized2


@pytest.mark.parametrize(
    "initial, added",
    [
        (
            "-",
            "+",
        ),
        (
            "+",
            "+",
        ),
        (
            "+-",
            "-+",
        ),
        (
            "+-",
            "++",
        ),
        (
            "--",
            "++",
        ),
        (
            "+--",
            "+--",
        ),
        (
            "-+",
            "-+",
        ),
        (
            "-+-",
            "-+-",
        ),
        (
            "-++",
            "-++",
        ),
        (
            "-++-",
            "-++-",
        ),
        (
            "-+++-",
            "-+++-",
        ),
        (
            "--++",
            "++--",
        ),
        (
            "-+-+-",
            "-+++-",
        ),
        (
            "+-+-+",
            "-+-+-",
        ),
        (
            "--+++---+++--",
            "++---+++---++",
        ),
        (
            "+--+",
            "--+-",
        ),
    ],
)
def test_partition_subset_with_partition_keys(initial: str, added: str):
    assert len(initial) == len(added)
    partitions_def = DailyPartitionsDefinition(start_date="2015-01-01")
    full_set_keys = partitions_def.get_partition_keys(
        current_time=datetime(year=2015, month=1, day=30)
    )[: len(initial)]
    initial_subset_keys = []
    added_subset_keys = []
    expected_keys_not_in_updated_subset = []
    for i in range(len(initial)):
        if initial[i] == "+":
            initial_subset_keys.append(full_set_keys[i])

        if added[i] == "+":
            added_subset_keys.append(full_set_keys[i])

        if initial[i] != "+" and added[i] != "+":
            expected_keys_not_in_updated_subset.append(full_set_keys[i])

    subset = TimeWindowPartitionsSubset.create_empty_subset(partitions_def).with_partition_keys(
        initial_subset_keys
    )
    assert all(partition_key in subset for partition_key in initial_subset_keys)
    updated_subset = cast(TimeWindowPartitionsSubset, subset.with_partition_keys(added_subset_keys))
    assert all(partition_key in updated_subset for partition_key in added_subset_keys)
    assert (
        updated_subset.get_partition_keys_not_in_subset(
            partitions_def=partitions_def,
            current_time=partitions_def.end_time_for_partition_key(full_set_keys[-1]),
        )
        == expected_keys_not_in_updated_subset
    )

    updated_subset_str = "".join(
        ("+" if (a == "+" or b == "+") else "-") for a, b in zip(initial, added)
    )
    expected_range_count = updated_subset_str.count("-+") + (
        1 if updated_subset_str[0] == "+" else 0
    )
    assert len(updated_subset.included_time_windows) == expected_range_count, updated_subset_str
    assert len(updated_subset) == updated_subset_str.count("+")


def test_weekly_time_window_partitions_subset():
    weekly_partitions_def = WeeklyPartitionsDefinition(start_date="2022-01-01")

    with_keys = ["2022-01-02", "2022-01-09", "2022-01-23", "2022-02-06"]
    subset = weekly_partitions_def.empty_subset().with_partition_keys(with_keys)
    assert set(subset.get_partition_keys()) == set(with_keys)


def test_time_window_partitions_subset_non_utc_timezone():
    weekly_partitions_def = DailyPartitionsDefinition(
        start_date="2022-01-01", timezone="America/Los_Angeles"
    )

    with_keys = ["2022-01-02", "2022-01-09", "2022-01-23", "2022-02-06"]
    subset = weekly_partitions_def.empty_subset().with_partition_keys(with_keys)
    assert set(subset.get_partition_keys()) == set(with_keys)


def test_time_window_partiitons_deserialize_backwards_compatible():
    serialized = "[[1420156800.0, 1420243200.0], [1420329600.0, 1420416000.0]]"
    partitions_def = DailyPartitionsDefinition(start_date="2015-01-01")
    deserialized = partitions_def.deserialize_subset(serialized)
    assert deserialized.get_partition_keys() == ["2015-01-02", "2015-01-04"]
    assert "2015-01-02" in deserialized

    serialized = (
        '{"time_windows": [[1420156800.0, 1420243200.0], [1420329600.0, 1420416000.0]],'
        ' "num_partitions": 2}'
    )
    deserialized = partitions_def.deserialize_subset(serialized)
    assert deserialized.get_partition_keys() == ["2015-01-02", "2015-01-04"]
    assert "2015-01-02" in deserialized


def test_current_time_window_partitions_serialization():
    partitions_def = DailyPartitionsDefinition(start_date="2015-01-01")
    serialized = (
        partitions_def.empty_subset().with_partition_keys(["2015-01-02", "2015-01-04"]).serialize()
    )
    deserialized = partitions_def.deserialize_subset(serialized)
    assert partitions_def.deserialize_subset(serialized)
    assert deserialized.get_partition_keys() == ["2015-01-02", "2015-01-04"]

    serialized = (
        '{"version": 1, "time_windows": [[1420156800.0, 1420243200.0], [1420329600.0,'
        ' 1420416000.0]], "num_partitions": 2}'
    )
    assert partitions_def.deserialize_subset(serialized)
    assert deserialized.get_partition_keys() == ["2015-01-02", "2015-01-04"]


def test_time_window_partitions_contains() -> None:
    partitions_def = DailyPartitionsDefinition(start_date="2015-01-01")
    keys = ["2015-01-06", "2015-01-07", "2015-01-08", "2015-01-10"]
    subset = TimeWindowPartitionsSubset.create_empty_subset(partitions_def).with_partition_keys(
        keys
    )
    for key in keys:
        assert key in subset

    assert "2015-01-05" not in subset
    assert "2015-01-09" not in subset
    assert "2015-01-11" not in subset
    assert None not in subset
    assert "<not a time string>" not in subset


def test_dst_transition_15_minute_partitions() -> None:
    partitions_def = TimeWindowPartitionsDefinition(
        cron_schedule="*/15 * * * *",
        start="2020-11-01-00:30",
        end="2020-11-01-2:30",
        timezone="US/Pacific",
        fmt="%Y-%m-%d-%H:%M",
    )
    subset = partitions_def.subset_with_all_partitions()
    assert set(subset.get_partition_keys()) == {
        "2020-11-01-00:30",
        "2020-11-01-00:45",
        "2020-11-01-01:00",
        "2020-11-01-01:15",
        "2020-11-01-01:30",
        "2020-11-01-01:45",
        "2020-11-01-01:00-0800",
        "2020-11-01-01:15-0800",
        "2020-11-01-01:30-0800",
        "2020-11-01-01:45-0800",
        "2020-11-01-02:00",
        "2020-11-01-02:15",
    }
    assert subset.get_partition_keys_not_in_subset(partitions_def) == []
    assert (
        partitions_def.deserialize_subset(subset.serialize()).get_partition_keys_not_in_subset(
            partitions_def
        )
        == []
    )


@pytest.mark.parametrize(
    "timezone, partition_key, expected",
    [
        ("US/Pacific", "2020-11-01-01:00", True),
        ("US/Pacific", "2020-11-01-01:00-0800", True),
        ("US/Pacific", "2020-11-01-02:00", True),
        ("US/Pacific", "2020-11-01-01:00-0700", False),
        ("US/Pacific", "2020-11-01-02:00-0800", False),
        (None, "2020-11-01-01:00", True),
        (None, "2020-11-01-02:00", True),
        (None, "2020-11-01-01:00-0700", False),
        (None, "2020-11-01-01:00-0800", False),
        (None, "2020-11-01-02:00-0800", False),
    ],
)
def test_dst_transition_has_partition_key(
    timezone: Optional[str], partition_key: str, expected: bool
) -> None:
    partitions_def = HourlyPartitionsDefinition("2020-10-01-00:00", timezone=timezone)
    assert partitions_def.has_partition_key(partition_key) == expected


def test_dst_transition_hourly_partitions() -> None:
    partitions_def = HourlyPartitionsDefinition(
        start_date="2020-10-31-23:00", end_date="2020-11-01-5:00", timezone="US/Pacific"
    )
    subset = partitions_def.subset_with_all_partitions()
    assert set(subset.get_partition_keys()) == {
        "2020-10-31-23:00",
        "2020-11-01-00:00",
        "2020-11-01-01:00",
        "2020-11-01-01:00-0800",
        "2020-11-01-02:00",
        "2020-11-01-03:00",
        "2020-11-01-04:00",
    }
    assert subset.get_partition_keys_not_in_subset(partitions_def) == []
    assert (
        partitions_def.deserialize_subset(subset.serialize()).get_partition_keys_not_in_subset(
            partitions_def
        )
        == []
    )


def test_dst_transition_hourly_partitions_with_utc_offset() -> None:
    partitions_def = HourlyPartitionsDefinition(
        start_date="2020-10-31-23:00:00-0700",
        end_date="2020-11-01-5:00:00-0800",
        timezone="US/Pacific",
        fmt="%Y-%m-%d-%H:%M:%S%z",
    )
    subset = partitions_def.subset_with_all_partitions()
    assert set(subset.get_partition_keys()) == {
        "2020-10-31-23:00:00-0700",
        "2020-11-01-00:00:00-0700",
        "2020-11-01-01:00:00-0700",
        "2020-11-01-01:00:00-0800",
        "2020-11-01-02:00:00-0800",
        "2020-11-01-03:00:00-0800",
        "2020-11-01-04:00:00-0800",
    }
    assert subset.get_partition_keys_not_in_subset(partitions_def) == []
    assert (
        partitions_def.deserialize_subset(subset.serialize()).get_partition_keys_not_in_subset(
            partitions_def
        )
        == []
    )


def test_dst_transition_daily_partitions() -> None:
    partitions_def = DailyPartitionsDefinition(
        start_date="2020-10-30-01:00",
        end_date="2020-11-03-01:00",
        timezone="US/Pacific",
        hour_offset=1,
        fmt="%Y-%m-%d-%H:%M",
    )
    subset = partitions_def.subset_with_all_partitions()
    assert set(subset.get_partition_keys()) == {
        "2020-10-30-01:00",
        "2020-10-31-01:00",
        "2020-11-01-01:00",
        "2020-11-02-01:00",
    }
    assert subset.get_partition_keys_not_in_subset(partitions_def) == []
    assert (
        partitions_def.deserialize_subset(subset.serialize()).get_partition_keys_not_in_subset(
            partitions_def
        )
        == []
    )


def test_unique_identifier():
    assert (
        DailyPartitionsDefinition(start_date="2015-01-01").get_serializable_unique_identifier()
        != DailyPartitionsDefinition(start_date="2015-01-02").get_serializable_unique_identifier()
    )
    assert (
        DailyPartitionsDefinition(start_date="2015-01-01").get_serializable_unique_identifier()
        == DailyPartitionsDefinition(start_date="2015-01-01").get_serializable_unique_identifier()
    )


def test_time_window_partition_len():
    partitions_def = HourlyPartitionsDefinition(start_date="2021-05-05-01:00", minute_offset=15)
    assert partitions_def.get_num_partitions() == len(partitions_def.get_partition_keys())
    assert (
        partitions_def.get_partition_keys_between_indexes(50, 51)
        == partitions_def.get_partition_keys()[50:51]
    )
    current_time = datetime.strptime("2021-05-07-03:15", "%Y-%m-%d-%H:%M")
    assert (
        partitions_def.get_partition_keys_between_indexes(50, 51, current_time=current_time)
        == partitions_def.get_partition_keys(current_time)[50:51]
    )

    @daily_partitioned_config(start_date="2021-05-01", end_offset=-2)
    def my_partitioned_config(_start, _end):
        return {}

    partitions_def = cast(TimeWindowPartitionsDefinition, my_partitioned_config.partitions_def)
    assert partitions_def.get_num_partitions() == len(partitions_def.get_partition_keys())
    assert (
        partitions_def.get_partition_keys_between_indexes(50, 53)
        == partitions_def.get_partition_keys()[50:53]
    )
    current_time = datetime.strptime("2021-06-23", "%Y-%m-%d")
    assert (
        partitions_def.get_partition_keys_between_indexes(50, 53, current_time=current_time)
        == partitions_def.get_partition_keys(current_time)[50:53]
    )

    weekly_partitions_def = WeeklyPartitionsDefinition(start_date="2022-01-01")
    assert weekly_partitions_def.get_num_partitions() == len(
        weekly_partitions_def.get_partition_keys()
    )
    current_time = datetime.strptime("2023-01-21", "%Y-%m-%d")
    assert (
        weekly_partitions_def.get_partition_keys_between_indexes(50, 53, current_time=current_time)
        == weekly_partitions_def.get_partition_keys(current_time)[50:53]
    )

    @daily_partitioned_config(start_date="2021-05-01", end_offset=2)
    def my_partitioned_config_2(_start, _end):
        return {}

    partitions_def = cast(TimeWindowPartitionsDefinition, my_partitioned_config_2.partitions_def)
    current_time = datetime.strptime("2021-06-20", "%Y-%m-%d")
    assert (
        partitions_def.get_partition_keys_between_indexes(50, 53, current_time=current_time)
        == partitions_def.get_partition_keys(current_time=current_time)[50:53]
    )

    partitions_def = TimeWindowPartitionsDefinition(
        cron_schedule="*/15 * * * *",
        start="2020-11-01-00:30",
        timezone="US/Pacific",
        fmt="%Y-%m-%d-%H:%M",
    )
    current_time = datetime.strptime("2021-06-20", "%Y-%m-%d")

    assert partitions_def.get_num_partitions(current_time) == len(
        partitions_def.get_partition_keys(current_time)
    )

    @daily_partitioned_config(start_date="2020-01-01", timezone="US/Pacific")
    def my_daily_dst_transition_partitioned_config(_start, _end):
        return {}

    partitions_def = cast(
        TimeWindowPartitionsDefinition, my_daily_dst_transition_partitioned_config.partitions_def
    )

    current_time_post_transition = datetime.strptime("2024-05-22", "%Y-%m-%d")

    assert partitions_def.get_num_partitions(current_time_post_transition) == len(
        partitions_def.get_partition_keys(current_time_post_transition)
    )

    current_time_pre_transition = datetime.strptime("2024-02-01", "%Y-%m-%d")

    assert partitions_def.get_num_partitions(current_time_pre_transition) == len(
        partitions_def.get_partition_keys(current_time_pre_transition)
    )


def test_get_first_partition_window():
    assert DailyPartitionsDefinition(
        start_date="2023-01-01"
    ).get_first_partition_window() == time_window("2023-01-01", "2023-01-02")

    assert DailyPartitionsDefinition(
        start_date="2023-01-01", end_offset=1
    ).get_first_partition_window(
        current_time=datetime.strptime("2023-01-01", "%Y-%m-%d")
    ) == time_window("2023-01-01", "2023-01-02")

    assert (
        DailyPartitionsDefinition(start_date="2023-02-15", end_offset=1).get_first_partition_window(
            current_time=datetime.strptime("2023-02-14", "%Y-%m-%d")
        )
        is None
    )

    assert DailyPartitionsDefinition(
        start_date="2023-01-01", end_offset=2
    ).get_first_partition_window(
        current_time=datetime.strptime("2023-01-02", "%Y-%m-%d")
    ) == time_window("2023-01-01", "2023-01-02")

    assert MonthlyPartitionsDefinition(
        start_date="2023-01-01", end_offset=1
    ).get_first_partition_window(
        current_time=datetime.strptime("2023-01-15", "%Y-%m-%d")
    ) == time_window("2023-01-01", "2023-02-01")

    assert (
        DailyPartitionsDefinition(
            start_date="2023-01-15", end_offset=-1
        ).get_first_partition_window(current_time=datetime.strptime("2023-01-16", "%Y-%m-%d"))
        is None
    )

    assert DailyPartitionsDefinition(
        start_date="2023-01-15", end_offset=-1
    ).get_first_partition_window(
        current_time=datetime.strptime("2023-01-17", "%Y-%m-%d")
    ) == time_window("2023-01-15", "2023-01-16")

    assert (
        DailyPartitionsDefinition(
            start_date="2023-01-15", end_offset=-2
        ).get_first_partition_window(current_time=datetime.strptime("2023-01-17", "%Y-%m-%d"))
        is None
    )

    assert DailyPartitionsDefinition(
        start_date="2023-01-15", end_offset=-2
    ).get_first_partition_window(
        current_time=datetime.strptime("2023-01-18", "%Y-%m-%d")
    ) == time_window("2023-01-15", "2023-01-16")

    assert (
        MonthlyPartitionsDefinition(
            start_date="2023-01-01", end_offset=-1
        ).get_first_partition_window(current_time=datetime.strptime("2023-01-15", "%Y-%m-%d"))
        is None
    )

    assert (
        DailyPartitionsDefinition(start_date="2023-01-15", end_offset=1).get_first_partition_window(
            current_time=datetime.strptime("2023-01-14", "%Y-%m-%d")
        )
        is None
    )

    assert DailyPartitionsDefinition(
        start_date="2023-01-15", end_offset=1
    ).get_first_partition_window(
        current_time=datetime(year=2023, month=1, day=15, hour=12, minute=0, second=0)
    ) == time_window("2023-01-15", "2023-01-16")

    assert DailyPartitionsDefinition(
        start_date="2023-01-15", end_offset=1
    ).get_first_partition_window(
        current_time=datetime(year=2023, month=1, day=14, hour=12, minute=0, second=0)
    ) == time_window("2023-01-15", "2023-01-16")

    assert (
        DailyPartitionsDefinition(start_date="2023-01-15", end_offset=1).get_first_partition_window(
            current_time=datetime(year=2023, month=1, day=13, hour=12, minute=0, second=0)
        )
        is None
    )

    assert (
        MonthlyPartitionsDefinition(
            start_date="2023-01-01", end_offset=-1
        ).get_first_partition_window(current_time=datetime.strptime("2023-01-15", "%Y-%m-%d"))
        is None
    )

    assert (
        MonthlyPartitionsDefinition(
            start_date="2023-01-01", end_offset=-1
        ).get_first_partition_window(current_time=datetime.strptime("2023-02-01", "%Y-%m-%d"))
        is None
    )

    assert MonthlyPartitionsDefinition(
        start_date="2023-01-01", end_offset=-1
    ).get_first_partition_window(
        current_time=datetime.strptime("2023-03-01", "%Y-%m-%d")
    ) == time_window("2023-01-01", "2023-02-01")


def test_invalid_cron_schedule():
    # creating a new partition definition with an invalid cron schedule should raise an error
    with pytest.raises(DagsterInvalidDefinitionError):
        TimeWindowPartitionsDefinition(
            start=parse_time_string("2021-05-05"),
            cron_schedule="0 -24 * * *",
            fmt=DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE,
        )


def test_get_cron_schedule_weekdays_with_hour_offset():
    partitions_def = TimeWindowPartitionsDefinition(
        start="2023-03-27", fmt="%Y-%m-%d", cron_schedule=r"0 0 * * 1-5"
    )
    with pytest.raises(
        CheckError,
        match="does not support minute_of_hour/hour_of_day/day_of_week/day_of_month arguments",
    ):
        partitions_def.get_cron_schedule(hour_of_day=3)


def test_has_partition_key():
    partitions_def = DailyPartitionsDefinition(start_date="2020-01-01")
    assert not partitions_def.has_partition_key("fdsjkl")
    assert not partitions_def.has_partition_key("2020-01-01 00:00")
    assert not partitions_def.has_partition_key("2020-01-01-00:00")
    assert not partitions_def.has_partition_key("2020/01/01")
    assert not partitions_def.has_partition_key("2019-12-31")
    assert not partitions_def.has_partition_key(
        "2020-03-15", current_time=datetime.strptime("2020-03-14", "%Y-%m-%d")
    )
    assert not partitions_def.has_partition_key(
        "2020-03-15", current_time=datetime.strptime("2020-03-15", "%Y-%m-%d")
    )
    assert partitions_def.has_partition_key("2020-01-01")
    assert partitions_def.has_partition_key("2020-03-15")


@pytest.mark.parametrize(
    "partitions_def,first_partition_window,last_partition_window,number_of_partitions,fmt",
    [
        (
            HourlyPartitionsDefinition(start_date="2022-01-01-00:00", end_date="2022-02-01-00:00"),
            ["2022-01-01-00:00", "2022-01-01-01:00"],
            ["2022-01-31-23:00", "2022-02-01-00:00"],
            744,
            "%Y-%m-%d-%H:%M",
        ),
        (
            DailyPartitionsDefinition(start_date="2022-01-01", end_date="2022-02-01"),
            ["2022-01-01", "2022-01-02"],
            ["2022-01-31", "2022-02-01"],
            31,
            "%Y-%m-%d",
        ),
        (
            WeeklyPartitionsDefinition(start_date="2022-01-01", end_date="2022-02-01"),
            [
                "2022-01-02",
                "2022-01-09",
            ],  # 2022-01-02 is Sunday, weekly cron starts from Sunday
            ["2022-01-23", "2022-01-30"],
            4,
            "%Y-%m-%d",
        ),
        (
            MonthlyPartitionsDefinition(start_date="2022-01-01", end_date="2023-01-01"),
            ["2022-01-01", "2022-02-01"],
            ["2022-12-01", "2023-01-01"],
            12,
            "%Y-%m-%d",
        ),
    ],
)
def test_partition_with_end_date(
    partitions_def: TimeWindowPartitionsDefinition,
    first_partition_window: Sequence[str],
    last_partition_window: Sequence[str],
    number_of_partitions: int,
    fmt: str,
):
    first_partition_window_ = TimeWindow(
        start=dst_safe_strptime(first_partition_window[0], partitions_def.timezone, fmt),
        end=dst_safe_strptime(first_partition_window[1], partitions_def.timezone, fmt),
    )

    last_partition_window_ = TimeWindow(
        start=dst_safe_strptime(last_partition_window[0], partitions_def.timezone, fmt),
        end=dst_safe_strptime(last_partition_window[1], partitions_def.timezone, fmt),
    )

    # get_last_partition_window
    assert partitions_def.get_last_partition_window() == last_partition_window_
    # get_next_partition_window
    assert partitions_def.get_next_partition_window(partitions_def.start) == first_partition_window_
    assert (
        partitions_def.get_next_partition_window(last_partition_window_.start)
        == last_partition_window_
    )
    assert not partitions_def.get_next_partition_window(last_partition_window_.end)
    assert len(partitions_def.get_partition_keys()) == number_of_partitions
    assert partitions_def.get_partition_keys()[0] == first_partition_window[0]
    assert partitions_def.get_partition_keys()[-1] == last_partition_window[0]
    # get_next_partition_key
    assert (
        partitions_def.get_next_partition_key(first_partition_window[0])
        == first_partition_window[1]
    )
    assert not partitions_def.get_next_partition_key(last_partition_window[0])
    # get_last_partition_key
    assert partitions_def.get_last_partition_key() == last_partition_window[0]
    # has_partition_key
    assert partitions_def.has_partition_key(first_partition_window[0])
    assert partitions_def.has_partition_key(last_partition_window[0])
    assert not partitions_def.has_partition_key(last_partition_window[1])


@pytest.mark.parametrize(
    "partitions_def",
    [
        (DailyPartitionsDefinition("2023-01-01", timezone="America/New_York")),
        (DailyPartitionsDefinition("2023-01-01")),
    ],
)
def test_time_window_partitions_def_serialization(partitions_def):
    time_window_partitions_def = TimeWindowPartitionsDefinition(
        start=partitions_def.start,
        end=partitions_def.end,
        cron_schedule="0 0 * * *",
        fmt="%Y-%m-%d",
        timezone=partitions_def.timezone,
        end_offset=partitions_def.end_offset,
    )
    deserialized = deserialize_value(serialize_value(time_window_partitions_def))
    assert deserialized == time_window_partitions_def
    assert deserialized.start.tzinfo == time_window_partitions_def.start.tzinfo  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]


def test_pickle_time_window_partitions_def():
    import datetime

    partitions_def = TimeWindowPartitionsDefinition(
        datetime.datetime(2021, 1, 1), "America/Los_Angeles", cron_schedule="0 0 * * *"
    )

    assert pickle.loads(pickle.dumps(partitions_def)) == partitions_def


def test_time_window_partitions_subset_add_partition_to_front() -> None:
    partitions_def = DailyPartitionsDefinition("2023-01-01")
    partition_keys_subset = partitions_def.subset_with_partition_keys({"2023-01-01"})
    time_windows_subset = TimeWindowPartitionsSubset(
        partitions_def,
        num_partitions=1,
        included_time_windows=[time_window("2023-01-02", "2023-01-03")],
    )

    combined = time_windows_subset | partition_keys_subset
    assert combined == partitions_def.subset_with_partition_keys({"2023-01-01", "2023-01-02"})


def test_get_partition_keys_not_in_subset_empty_subset() -> None:
    # starts in the future
    partitions_def = DailyPartitionsDefinition("2024-01-01")
    time_windows_subset = TimeWindowPartitionsSubset(
        partitions_def, num_partitions=0, included_time_windows=[]
    )
    with freeze_time(create_datetime(2023, 1, 1)):
        assert time_windows_subset.get_partition_keys_not_in_subset(partitions_def) == []


@pytest.mark.parametrize(
    "subtractor,subtractee,result",
    [
        (  # Subtractee earlier than subtractor
            persisted_time_window("2019-02-27", "2025-04-01"),
            persisted_time_window("2019-01-02", "2019-01-03"),
            [persisted_time_window("2019-02-27", "2025-04-01")],
        ),
        (  # Subtractee later than subtractor
            persisted_time_window("2019-02-27", "2025-04-01"),
            persisted_time_window("2025-05-01", "2026-01-01"),
            [persisted_time_window("2019-02-27", "2025-04-01")],
        ),
        (  # Subtractee <= subtractor
            persisted_time_window("2019-02-27", "2025-04-01"),
            persisted_time_window("2019-01-02", "2019-02-27"),
            [persisted_time_window("2019-02-27", "2025-04-01")],
        ),
        (  # Subtractee >= subtractor
            persisted_time_window("2019-02-27", "2025-04-01"),
            persisted_time_window("2025-04-01", "2026-01-01"),
            [persisted_time_window("2019-02-27", "2025-04-01")],
        ),
        (  # Subtractee == subtractor
            persisted_time_window("2019-02-27", "2025-04-01"),
            persisted_time_window("2019-02-27", "2025-04-01"),
            [],
        ),
        (  # Subtractee fully covers subtractor
            persisted_time_window("2019-02-27", "2025-04-01"),
            persisted_time_window("2018-02-27", "2026-04-01"),
            [],
        ),
        (  # Subtractee overlaps left part of subtractor
            persisted_time_window("2019-02-27", "2025-04-01"),
            persisted_time_window("2019-02-27", "2024-01-01"),
            [
                persisted_time_window("2024-01-01", "2025-04-01"),
            ],
        ),
        (  # Subtractee overlaps left part of subtractor, extends earlier
            persisted_time_window("2019-02-27", "2025-04-01"),
            persisted_time_window("2018-02-27", "2024-01-01"),
            [
                persisted_time_window("2024-01-01", "2025-04-01"),
            ],
        ),
        (  # Subtractee overlaps right part of subtractor
            persisted_time_window("2019-02-27", "2025-04-01"),
            persisted_time_window("2021-02-27", "2025-04-01"),
            [
                persisted_time_window("2019-02-27", "2021-02-27"),
            ],
        ),
        (  # Subtractee overlaps right part of subtractor, extends later
            persisted_time_window("2019-02-27", "2025-04-01"),
            persisted_time_window("2021-02-27", "2026-04-01"),
            [
                persisted_time_window("2019-02-27", "2021-02-27"),
            ],
        ),
        (  # Subtractee breaks subtractor into two
            persisted_time_window("2019-02-27", "2025-04-01"),
            persisted_time_window("2021-02-27", "2023-04-01"),
            [
                persisted_time_window("2019-02-27", "2021-02-27"),
                persisted_time_window("2023-04-01", "2025-04-01"),
            ],
        ),
    ],
)
def test_persisted_time_window_subtract(subtractor, subtractee, result):
    assert subtractor.subtract(subtractee) == result


@pytest.mark.parametrize(
    "subtractor,subtractee,result",
    [
        (
            [
                persisted_time_window("2019-02-27", "2019-12-31"),
                persisted_time_window("2022-06-29", "2022-12-31"),
                persisted_time_window("2023-01-01", "2024-12-31"),
            ],
            [
                # does nothing, is just happy to be here
                persisted_time_window("2017-01-01", "2018-01-01"),
                # fully consumes the first two windows and part of the third window
                persisted_time_window("2019-01-01", "2023-12-31"),
                # also does nothing, too late
                persisted_time_window("2025-01-01", "2026-01-01"),
            ],
            [persisted_time_window("2023-12-31", "2024-12-31")],
        ),
        (
            [
                persisted_time_window("2019-02-27", "2019-12-31"),
                persisted_time_window("2022-06-29", "2022-12-31"),
            ],
            [  # splits the first window in two
                persisted_time_window("2019-06-01", "2019-07-01"),
                # splits the newly split second window into two as well
                persisted_time_window("2019-10-01", "2019-11-01"),
            ],
            [
                persisted_time_window("2019-02-27", "2019-06-01"),
                persisted_time_window("2019-07-01", "2019-10-01"),
                persisted_time_window("2019-11-01", "2019-12-31"),
                persisted_time_window("2022-06-29", "2022-12-31"),
            ],
        ),
        (
            [],  # nothing comes from nothing, nothing ever could
            [],
            [],
        ),
        (
            [
                persisted_time_window("2019-02-27", "2019-12-31"),
                persisted_time_window("2022-06-29", "2022-12-31"),
                persisted_time_window("2023-01-01", "2024-12-31"),
            ],
            [],  # subtracting nothing leaves you with the same thing
            [
                persisted_time_window("2019-02-27", "2019-12-31"),
                persisted_time_window("2022-06-29", "2022-12-31"),
                persisted_time_window("2023-01-01", "2024-12-31"),
            ],
        ),
        (
            [  # subtracting yourself from yourself leaves you with nothing
                persisted_time_window("2019-02-27", "2019-12-31"),
                persisted_time_window("2022-06-29", "2022-12-31"),
                persisted_time_window("2023-01-01", "2024-12-31"),
            ],
            [
                persisted_time_window("2019-02-27", "2019-12-31"),
                persisted_time_window("2022-06-29", "2022-12-31"),
                persisted_time_window("2023-01-01", "2024-12-31"),
            ],
            [],
        ),
    ],
)
def test_asset_subset_subtract(subtractor, subtractee, result):
    partitions_def = DailyPartitionsDefinition("2015-01-01")

    subtractor_subset = TimeWindowPartitionsSubset(
        partitions_def, num_partitions=None, included_time_windows=subtractor
    )

    subtractee_subset = TimeWindowPartitionsSubset(
        partitions_def, num_partitions=None, included_time_windows=subtractee
    )

    assert subtractor_subset - subtractee_subset == TimeWindowPartitionsSubset(
        partitions_def, num_partitions=None, included_time_windows=result
    )


@pytest.mark.parametrize(
    "a,b,result",
    [
        (
            [
                persisted_time_window("2019-02-27", "2019-12-31"),
                persisted_time_window("2022-06-29", "2022-12-31"),
                persisted_time_window("2023-01-01", "2024-12-31"),
            ],
            [
                # does nothing, is just happy to be here
                persisted_time_window("2017-01-01", "2018-01-01"),
                # fully intersects the first two windows and part of the third
                persisted_time_window("2019-01-01", "2023-12-31"),
                # also does nothing, too late
                persisted_time_window("2025-01-01", "2026-01-01"),
            ],
            [
                persisted_time_window("2019-02-27", "2019-12-31"),
                persisted_time_window("2022-06-29", "2022-12-31"),
                persisted_time_window("2023-01-01", "2023-12-31"),
            ],
        ),
        (
            [
                persisted_time_window("2019-02-27", "2019-12-31"),
                persisted_time_window("2022-06-29", "2022-12-31"),
            ],
            [
                # takes a chunk out of the first window
                persisted_time_window("2019-06-01", "2019-07-01"),
                # also takes a chunk out of the first window
                persisted_time_window("2019-10-01", "2019-11-01"),
                # overlaps both the first and second window
                persisted_time_window("2019-11-15", "2022-08-16"),
            ],
            [
                persisted_time_window("2019-06-01", "2019-07-01"),
                persisted_time_window("2019-10-01", "2019-11-01"),
                persisted_time_window("2019-11-15", "2019-12-31"),
                persisted_time_window("2022-06-29", "2022-08-16"),
            ],
        ),
    ],
)
def test_asset_subset_and(a, b, result) -> None:
    partitions_def = DailyPartitionsDefinition("2015-01-01")

    a_subset = TimeWindowPartitionsSubset(
        partitions_def, num_partitions=None, included_time_windows=a
    )

    b_subset = TimeWindowPartitionsSubset(
        partitions_def, num_partitions=None, included_time_windows=b
    )

    assert a_subset & b_subset == TimeWindowPartitionsSubset(
        partitions_def, num_partitions=None, included_time_windows=result
    )


@pytest.mark.parametrize(
    "a,b,result",
    [
        (
            [
                persisted_time_window("2019-02-27", "2019-12-31"),
                persisted_time_window("2022-06-29", "2022-12-31"),
                persisted_time_window("2023-01-01", "2024-12-31"),
            ],
            [
                # no intersection
                persisted_time_window("2017-01-01", "2018-01-01"),
                # fully intersects the first two windows and part of the third
                persisted_time_window("2019-01-01", "2023-12-31"),
                # no intersection
                persisted_time_window("2025-01-01", "2026-01-01"),
            ],
            [
                persisted_time_window("2017-01-01", "2018-01-01"),
                persisted_time_window("2019-01-01", "2024-12-31"),
                persisted_time_window("2025-01-01", "2026-01-01"),
            ],
        ),
        (
            [
                persisted_time_window("2019-02-27", "2019-12-31"),
                persisted_time_window("2022-06-29", "2022-12-31"),
            ],
            [
                # intersects with the first window
                persisted_time_window("2019-06-01", "2019-07-01"),
                # also intersects with the first window
                persisted_time_window("2019-10-01", "2019-11-01"),
                # overlaps both the first and second window
                persisted_time_window("2019-11-15", "2022-08-16"),
            ],
            [
                persisted_time_window("2019-02-27", "2022-12-31"),
            ],
        ),
    ],
)
def test_asset_subset_or(a, b, result) -> None:
    partitions_def = DailyPartitionsDefinition("2015-01-01")

    a_subset = TimeWindowPartitionsSubset(
        partitions_def, num_partitions=None, included_time_windows=a
    )

    b_subset = TimeWindowPartitionsSubset(
        partitions_def, num_partitions=None, included_time_windows=b
    )

    assert a_subset | b_subset == TimeWindowPartitionsSubset(
        partitions_def, num_partitions=None, included_time_windows=result
    )


def test_persisted_time_window_serdes():
    serialized_time_window = '{"__class__": "TimeWindow", "end": {"__class__": "TimestampWithTimezone", "timestamp": 1717680319.16809, "timezone": "America/Chicago"}, "start": {"__class__": "TimestampWithTimezone", "timestamp": 1717593919.168011, "timezone": "America/Chicago"}}'
    deserialized_time_window = deserialize_value(serialized_time_window, PersistedTimeWindow)
    assert isinstance(deserialized_time_window, PersistedTimeWindow)
    assert serialize_value(deserialized_time_window) == serialized_time_window
