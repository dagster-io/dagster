from datetime import datetime
from typing import cast

import pendulum.parser
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
from dagster._core.definitions.time_window_partitions import (
    ScheduleType,
    TimeWindow,
    TimeWindowPartitionsSubset,
)
from dagster._utils.partitions import DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE

DATE_FORMAT = "%Y-%m-%d"


def time_window(start: str, end: str) -> TimeWindow:
    return TimeWindow(
        cast(datetime, pendulum.parser.parse(start)), cast(datetime, pendulum.parser.parse(end))
    )


def test_daily_partitions():
    @daily_partitioned_config(start_date="2021-05-05")
    def my_partitioned_config(_start, _end):
        return {}

    partitions_def = my_partitioned_config.partitions_def
    assert partitions_def == DailyPartitionsDefinition(start_date="2021-05-05")
    assert partitions_def.get_next_partition_key("2021-05-05") == "2021-05-06"
    assert (
        partitions_def.get_last_partition_key(pendulum.parser.parse("2021-05-06")) == "2021-05-05"
    )
    assert (
        partitions_def.get_last_partition_key(pendulum.parser.parse("2021-05-06").add(minutes=1))
        == "2021-05-05"
    )
    assert (
        partitions_def.get_last_partition_key(
            pendulum.parser.parse("2021-05-07").subtract(minutes=1)
        )
        == "2021-05-05"
    )
    assert partitions_def.schedule_type == ScheduleType.DAILY

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
    assert partitions_def.minute_offset == 15
    assert partitions_def.hour_offset == 3
    assert partitions_def.day_offset == 12
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


def test_twice_daily_partitions():
    partitions_def = TimeWindowPartitionsDefinition(
        start=pendulum.parse("2021-05-05"),
        cron_schedule="0 0,11 * * *",
        fmt=DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE,
    )

    assert [
        partition.value
        for partition in partitions_def.get_partitions(datetime.strptime("2021-05-07", DATE_FORMAT))
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
        start=pendulum.parse("2021-05-05"),
        cron_schedule="0 7 * * *",
        fmt=DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE,
    )

    assert [
        partition.value
        for partition in partitions_def.get_partitions(datetime.strptime("2021-05-08", DATE_FORMAT))
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
        TimeWindowPartitionsSubset, partitions_def.empty_subset().with_partition_keys(subset_keys)
    )
    for partition_key in subset_keys:
        assert partition_key in subset
    assert (
        subset.get_partition_keys_not_in_subset(
            current_time=partitions_def.end_time_for_partition_key(full_set_keys[-1])
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

    subset = partitions_def.empty_subset().with_partition_keys(initial_subset_keys)
    assert all(partition_key in subset for partition_key in initial_subset_keys)
    updated_subset = cast(TimeWindowPartitionsSubset, subset.with_partition_keys(added_subset_keys))
    assert all(partition_key in updated_subset for partition_key in added_subset_keys)
    assert (
        updated_subset.get_partition_keys_not_in_subset(
            current_time=partitions_def.end_time_for_partition_key(full_set_keys[-1])
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


def test_time_window_partitions_contains():
    partitions_def = DailyPartitionsDefinition(start_date="2015-01-01")
    keys = ["2015-01-06", "2015-01-07", "2015-01-08", "2015-01-10"]
    subset = partitions_def.empty_subset().with_partition_keys(keys)
    for key in keys:
        assert key in subset

    assert "2015-01-05" not in subset
    assert "2015-01-09" not in subset
    assert "2015-01-11" not in subset


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
    assert partitions_def.get_num_partitions() == len(partitions_def.get_partitions())
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


def test_get_first_partition_window():
    assert DailyPartitionsDefinition(
        start_date="2023-01-01"
    ).get_first_partition_window() == time_window("2023-01-01", "2023-01-02")

    assert DailyPartitionsDefinition(
        start_date="2023-01-01", end_offset=1
    ).get_first_partition_window(
        current_time=datetime.strptime("2023-01-01", "%Y-%m-%d")
    ) == time_window(
        "2023-01-01", "2023-01-02"
    )

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
    ) == time_window(
        "2023-01-01", "2023-01-02"
    )

    assert MonthlyPartitionsDefinition(
        start_date="2023-01-01", end_offset=1
    ).get_first_partition_window(
        current_time=datetime.strptime("2023-01-15", "%Y-%m-%d")
    ) == time_window(
        "2023-01-01", "2023-02-01"
    )

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
    ) == time_window(
        "2023-01-15", "2023-01-16"
    )

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
    ) == time_window(
        "2023-01-15", "2023-01-16"
    )

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
    ) == time_window(
        "2023-01-15", "2023-01-16"
    )

    assert DailyPartitionsDefinition(
        start_date="2023-01-15", end_offset=1
    ).get_first_partition_window(
        current_time=datetime(year=2023, month=1, day=14, hour=12, minute=0, second=0)
    ) == time_window(
        "2023-01-15", "2023-01-16"
    )

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
    ) == time_window(
        "2023-01-01", "2023-02-01"
    )


def test_invalid_cron_schedule():
    # creating a new partition definition with an invalid cron schedule should raise an error
    with pytest.raises(DagsterInvalidDefinitionError):
        TimeWindowPartitionsDefinition(
            start=pendulum.parse("2021-05-05"),
            cron_schedule="0 -24 * * *",
            fmt=DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE,
        )
