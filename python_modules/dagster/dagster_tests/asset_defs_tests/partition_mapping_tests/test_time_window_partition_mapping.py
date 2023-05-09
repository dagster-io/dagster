from datetime import datetime, timezone
from typing import Optional, Sequence

import pendulum
import pytest
from dagster import (
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
    MonthlyPartitionsDefinition,
    TimeWindow,
    TimeWindowPartitionMapping,
    TimeWindowPartitionsDefinition,
    WeeklyPartitionsDefinition,
)
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.errors import DagsterInvalidInvocationError


def subset_with_keys(partitions_def: TimeWindowPartitionsDefinition, keys: Sequence[str]):
    return partitions_def.empty_subset().with_partition_keys(keys)


def subset_with_key_range(partitions_def: TimeWindowPartitionsDefinition, start: str, end: str):
    return partitions_def.empty_subset().with_partition_keys(
        partitions_def.get_partition_keys_in_range(PartitionKeyRange(start, end))
    )


def test_get_upstream_partitions_for_partition_range_same_partitioning():
    downstream_partitions_def = DailyPartitionsDefinition(start_date="2021-05-05")
    upstream_partitions_def = DailyPartitionsDefinition(start_date="2021-05-05")
    # single partition key
    result = TimeWindowPartitionMapping().get_upstream_partitions_for_partitions(
        subset_with_keys(downstream_partitions_def, ["2021-05-07"]),
        upstream_partitions_def,
    )
    assert result == upstream_partitions_def.empty_subset().with_partition_keys(["2021-05-07"])

    # range of partition keys
    result = TimeWindowPartitionMapping().get_upstream_partitions_for_partitions(
        subset_with_key_range(downstream_partitions_def, "2021-05-07", "2021-05-09"),
        upstream_partitions_def,
    )
    assert result == subset_with_key_range(upstream_partitions_def, "2021-05-07", "2021-05-09")


def test_get_upstream_partitions_for_partition_range_same_partitioning_different_formats():
    downstream_partitions_def = DailyPartitionsDefinition(start_date="2021-05-05")
    upstream_partitions_def = DailyPartitionsDefinition(start_date="2021/05/05", fmt="%Y/%m/%d")

    result = TimeWindowPartitionMapping().get_upstream_partitions_for_partitions(
        subset_with_key_range(downstream_partitions_def, "2021-05-07", "2021-05-09"),
        upstream_partitions_def,
    )
    assert result == subset_with_key_range(upstream_partitions_def, "2021/05/07", "2021/05/09")
    assert result.get_partition_keys() == upstream_partitions_def.get_partition_keys_in_range(
        PartitionKeyRange("2021/05/07", "2021/05/09")
    )


def test_get_upstream_partitions_for_partition_range_hourly_downstream_daily_upstream():
    downstream_partitions_def = HourlyPartitionsDefinition(start_date="2021-05-05-00:00")
    upstream_partitions_def = DailyPartitionsDefinition(start_date="2021-05-05")
    result = TimeWindowPartitionMapping().get_upstream_partitions_for_partitions(
        subset_with_keys(downstream_partitions_def, ["2021-05-07-05:00"]),
        upstream_partitions_def,
    )
    assert result == upstream_partitions_def.empty_subset().with_partition_keys(["2021-05-07"])

    result = TimeWindowPartitionMapping().get_upstream_partitions_for_partitions(
        subset_with_key_range(downstream_partitions_def, "2021-05-07-05:00", "2021-05-09-09:00"),
        upstream_partitions_def,
    )
    assert result.get_partition_keys() == upstream_partitions_def.get_partition_keys_in_range(
        PartitionKeyRange("2021-05-07", "2021-05-09")
    )


def test_get_upstream_partitions_for_partition_range_daily_downstream_hourly_upstream():
    downstream_partitions_def = DailyPartitionsDefinition(start_date="2021-05-05")
    upstream_partitions_def = HourlyPartitionsDefinition(start_date="2021-05-05-00:00")
    result = TimeWindowPartitionMapping().get_upstream_partitions_for_partitions(
        subset_with_keys(downstream_partitions_def, ["2021-05-07"]),
        upstream_partitions_def,
    )
    assert result.get_partition_keys() == upstream_partitions_def.get_partition_keys_in_range(
        PartitionKeyRange("2021-05-07-00:00", "2021-05-07-23:00")
    )

    result = TimeWindowPartitionMapping().get_upstream_partitions_for_partitions(
        subset_with_key_range(downstream_partitions_def, "2021-05-07", "2021-05-09"),
        upstream_partitions_def,
    )
    assert result.get_partition_keys() == upstream_partitions_def.get_partition_keys_in_range(
        PartitionKeyRange("2021-05-07-00:00", "2021-05-09-23:00")
    )


def test_get_upstream_partitions_for_partition_range_monthly_downstream_daily_upstream():
    downstream_partitions_def = MonthlyPartitionsDefinition(start_date="2021-05-01")
    upstream_partitions_def = DailyPartitionsDefinition(start_date="2021-05-01")
    result = TimeWindowPartitionMapping().get_upstream_partitions_for_partitions(
        subset_with_key_range(downstream_partitions_def, "2021-05-01", "2021-07-01"),
        upstream_partitions_def,
    )
    assert result.get_partition_keys() == upstream_partitions_def.get_partition_keys_in_range(
        PartitionKeyRange("2021-05-01", "2021-07-31")
    )


def test_get_upstream_partitions_for_partition_range_twice_daily_downstream_daily_upstream():
    start = datetime(year=2020, month=1, day=5)
    downstream_partitions_def = TimeWindowPartitionsDefinition(
        cron_schedule="0 0 * * *", start=start, fmt="%Y-%m-%d"
    )
    upstream_partitions_def = TimeWindowPartitionsDefinition(
        cron_schedule="0 0,11 * * *", start=start, fmt="%Y-%m-%d %H:%M"
    )
    result = TimeWindowPartitionMapping().get_upstream_partitions_for_partitions(
        subset_with_key_range(downstream_partitions_def, "2021-05-01", "2021-05-03"),
        upstream_partitions_def,
    )
    assert result.get_partition_keys() == upstream_partitions_def.get_partition_keys_in_range(
        PartitionKeyRange("2021-05-01 00:00", "2021-05-03 11:00")
    )


def test_get_upstream_partitions_for_partition_range_daily_downstream_twice_daily_upstream():
    start = datetime(year=2020, month=1, day=5)
    downstream_partitions_def = TimeWindowPartitionsDefinition(
        cron_schedule="0 0,11 * * *", start=start, fmt="%Y-%m-%d %H:%M"
    )
    upstream_partitions_def = TimeWindowPartitionsDefinition(
        cron_schedule="0 0 * * *", start=start, fmt="%Y-%m-%d"
    )
    result = TimeWindowPartitionMapping().get_upstream_partitions_for_partitions(
        subset_with_key_range(downstream_partitions_def, "2021-05-01 00:00", "2021-05-03 00:00"),
        upstream_partitions_def,
    )
    assert result.get_partition_keys() == upstream_partitions_def.get_partition_keys_in_range(
        PartitionKeyRange("2021-05-01", "2021-05-03")
    )


def test_get_upstream_partitions_for_partition_range_daily_non_aligned():
    start = datetime(year=2020, month=1, day=5)
    downstream_partitions_def = TimeWindowPartitionsDefinition(
        cron_schedule="0 0 * * *", start=start, fmt="%Y-%m-%d"
    )
    upstream_partitions_def = TimeWindowPartitionsDefinition(
        cron_schedule="0 11 * * *", start=start, fmt="%Y-%m-%d"
    )
    result = TimeWindowPartitionMapping().get_upstream_partitions_for_partitions(
        subset_with_key_range(downstream_partitions_def, "2021-05-02", "2021-05-04"),
        upstream_partitions_def,
    )
    assert result.get_partition_keys() == upstream_partitions_def.get_partition_keys_in_range(
        PartitionKeyRange("2021-05-01", "2021-05-04")
    )


def test_get_upstream_partitions_for_partition_range_weekly_with_offset():
    partitions_def = WeeklyPartitionsDefinition(
        start_date="2022-09-04", day_offset=0, hour_offset=10
    )

    result = TimeWindowPartitionMapping().get_upstream_partitions_for_partitions(
        subset_with_key_range(partitions_def, "2022-09-11", "2022-09-11"),
        partitions_def,
    )
    assert result.get_partition_keys() == (
        partitions_def.get_partition_keys_in_range(PartitionKeyRange("2022-09-11", "2022-09-11"))
    )


def test_daily_to_daily_lag():
    downstream_partitions_def = upstream_partitions_def = DailyPartitionsDefinition(
        start_date="2021-05-05"
    )
    mapping = TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)

    # single partition key
    assert mapping.get_upstream_partitions_for_partitions(
        subset_with_keys(downstream_partitions_def, ["2021-05-07"]), upstream_partitions_def
    ).get_partition_keys() == ["2021-05-06"]

    assert mapping.get_downstream_partitions_for_partitions(
        subset_with_keys(upstream_partitions_def, ["2021-05-06"]), downstream_partitions_def
    ).get_partition_keys() == ["2021-05-07"]

    # first partition key
    assert (
        mapping.get_upstream_partitions_for_partitions(
            subset_with_keys(downstream_partitions_def, ["2021-05-05"]), upstream_partitions_def
        ).get_partition_keys()
        == []
    )

    # range of partition keys
    assert mapping.get_upstream_partitions_for_partitions(
        subset_with_key_range(downstream_partitions_def, "2021-05-07", "2021-05-09"),
        upstream_partitions_def,
    ).get_partition_keys() == ["2021-05-06", "2021-05-07", "2021-05-08"]

    assert mapping.get_downstream_partitions_for_partitions(
        subset_with_key_range(downstream_partitions_def, "2021-05-06", "2021-05-08"),
        downstream_partitions_def,
    ).get_partition_keys() == ["2021-05-07", "2021-05-08", "2021-05-09"]

    # range overlaps start
    assert mapping.get_upstream_partitions_for_partitions(
        subset_with_key_range(downstream_partitions_def, "2021-05-05", "2021-05-07"),
        upstream_partitions_def,
    ).get_partition_keys() == ["2021-05-05", "2021-05-06"]


def test_daily_to_daily_lag_different_start_date():
    upstream_partitions_def = DailyPartitionsDefinition(start_date="2021-05-05")
    downstream_partitions_def = DailyPartitionsDefinition(start_date="2021-05-06")
    mapping = TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)

    assert mapping.get_upstream_partitions_for_partitions(
        subset_with_keys(downstream_partitions_def, ["2021-05-06"]), upstream_partitions_def
    ).get_partition_keys() == ["2021-05-05"]

    assert mapping.get_downstream_partitions_for_partitions(
        subset_with_keys(upstream_partitions_def, ["2021-05-05"]), downstream_partitions_def
    ).get_partition_keys() == ["2021-05-06"]


@pytest.mark.parametrize(
    "upstream_partitions_def,downstream_partitions_def,upstream_keys,expected_downstream_keys,current_time",
    [
        (
            HourlyPartitionsDefinition(start_date="2021-05-05-00:00"),
            DailyPartitionsDefinition(start_date="2021-05-05"),
            ["2021-05-05-00:00"],
            [],
            datetime(2021, 5, 5, 1),
        ),
        (
            HourlyPartitionsDefinition(start_date="2021-05-05-00:00"),
            DailyPartitionsDefinition(start_date="2021-05-05"),
            ["2021-05-05-23:00", "2021-05-06-00:00", "2021-05-06-01:00"],
            ["2021-05-05"],
            datetime(2021, 5, 6, 1),
        ),
        (
            HourlyPartitionsDefinition(start_date="2021-05-05-00:00"),
            DailyPartitionsDefinition(start_date="2021-05-05"),
            ["2021-05-05-23:00", "2021-05-06-00:00", "2021-05-06-01:00"],
            ["2021-05-05", "2021-05-06"],
            None,
        ),
        (
            HourlyPartitionsDefinition(start_date="2021-05-05-00:00", timezone="US/Central"),
            DailyPartitionsDefinition(start_date="2021-05-05", timezone="US/Central"),
            ["2021-05-05-23:00", "2021-05-06-00:00", "2021-05-06-01:00"],
            ["2021-05-05"],
            datetime(2021, 5, 6, 6, tzinfo=timezone.utc),
        ),
        (
            HourlyPartitionsDefinition(start_date="2021-05-05-00:00"),
            DailyPartitionsDefinition(start_date="2021-05-05", end_offset=1),
            ["2021-05-05-23:00", "2021-05-06-00:00", "2021-05-06-01:00"],
            ["2021-05-05", "2021-05-06"],
            datetime(2021, 5, 6, 1),
        ),
        (
            DailyPartitionsDefinition(start_date="2022-01-01"),
            DailyPartitionsDefinition(start_date="2021-01-01"),
            ["2021-12-31"],
            [],
            datetime(2022, 1, 1, 1),
        ),
        (
            DailyPartitionsDefinition(start_date="2022-01-01"),
            DailyPartitionsDefinition(start_date="2021-01-01"),
            ["2021-12-30"],
            [],
            datetime(2022, 12, 31, 1),
        ),
        (
            DailyPartitionsDefinition(start_date="2022-01-01"),
            DailyPartitionsDefinition(start_date="2021-01-01"),
            ["2022-12-30"],
            ["2022-12-30"],
            datetime(2022, 12, 31, 1),
        ),
        (
            DailyPartitionsDefinition(start_date="2022-01-01"),
            DailyPartitionsDefinition(start_date="2021-01-01"),
            ["2022-12-30", "2022-12-31", "2023-01-01", "2023-01-02"],
            ["2022-12-30", "2022-12-31", "2023-01-01"],
            datetime(2023, 1, 2, 1),
        ),
    ],
)
def test_get_downstream_with_current_time(
    upstream_partitions_def: TimeWindowPartitionsDefinition,
    downstream_partitions_def: TimeWindowPartitionsDefinition,
    upstream_keys: Sequence[str],
    expected_downstream_keys: Sequence[str],
    current_time: Optional[datetime],
):
    mapping = TimeWindowPartitionMapping()
    assert (
        mapping.get_downstream_partitions_for_partitions(
            subset_with_keys(upstream_partitions_def, upstream_keys),
            downstream_partitions_def,
            current_time=current_time,
        ).get_partition_keys()
        == expected_downstream_keys
    )


@pytest.mark.parametrize(
    "upstream_partitions_def,downstream_partitions_def,expected_upstream_keys,downstream_keys,current_time,error_expected",
    [
        (
            DailyPartitionsDefinition(start_date="2021-05-05"),
            HourlyPartitionsDefinition(start_date="2021-05-05-00:00"),
            [],
            ["2021-06-01-00:00"],
            datetime(2021, 6, 1, 1),
            True,
        ),
        (
            DailyPartitionsDefinition(start_date="2021-05-05"),
            HourlyPartitionsDefinition(start_date="2021-05-05-00:00"),
            [],
            ["2021-05-05-23:00", "2021-05-06-00:00", "2021-05-06-01:00"],
            datetime(2021, 5, 6, 1),
            True,
        ),
        (
            DailyPartitionsDefinition(start_date="2021-05-05"),
            HourlyPartitionsDefinition(start_date="2021-05-05-00:00"),
            ["2021-05-05"],
            ["2021-05-05-23:00"],
            datetime(2021, 5, 6, 1),
            False,
        ),
        (
            DailyPartitionsDefinition(start_date="2021-05-05", timezone="US/Central"),
            HourlyPartitionsDefinition(start_date="2021-05-05-00:00", timezone="US/Central"),
            ["2021-05-05"],
            ["2021-05-05-23:00"],
            datetime(2021, 5, 6, 5, tzinfo=timezone.utc),  # 2021-05-06-00:00 in US/Central
            False,
        ),
        (
            DailyPartitionsDefinition(start_date="2021-05-05", timezone="US/Central"),
            HourlyPartitionsDefinition(start_date="2021-05-05-00:00", timezone="US/Central"),
            [],
            ["2021-05-05-23:00"],
            datetime(2021, 5, 6, 4, tzinfo=timezone.utc),  # 2021-05-05-23:00 in US/Central
            True,
        ),
        (
            DailyPartitionsDefinition(start_date="2021-05-05", end_offset=1),
            HourlyPartitionsDefinition(start_date="2021-05-05-00:00"),
            ["2021-05-05", "2021-05-06"],
            ["2021-05-05-23:00", "2021-05-06-00:00", "2021-05-06-01:00"],
            datetime(2021, 5, 6, 1),
            False,
        ),
        (
            DailyPartitionsDefinition(start_date="2022-01-01"),
            DailyPartitionsDefinition(start_date="2021-01-01"),
            [],
            ["2021-06-06"],
            datetime(2022, 1, 6, 1),
            True,
        ),
        (
            DailyPartitionsDefinition(start_date="2022-01-01"),
            DailyPartitionsDefinition(start_date="2021-01-01"),
            ["2022-01-01"],
            ["2022-01-01"],
            datetime(2022, 1, 6, 1),
            False,
        ),
        (
            DailyPartitionsDefinition(start_date="2022-01-01"),
            DailyPartitionsDefinition(start_date="2021-01-01"),
            [],
            ["2021-12-31"],
            datetime(2022, 1, 6, 1),
            True,
        ),
        (
            DailyPartitionsDefinition(start_date="2022-01-01"),
            DailyPartitionsDefinition(start_date="2021-01-01"),
            [],
            ["2021-12-30"],
            datetime(2021, 12, 31, 1),
            True,
        ),
    ],
)
def test_get_upstream_with_current_time(
    upstream_partitions_def: TimeWindowPartitionsDefinition,
    downstream_partitions_def: TimeWindowPartitionsDefinition,
    expected_upstream_keys: Sequence[str],
    downstream_keys: Sequence[str],
    current_time: Optional[datetime],
    error_expected: bool,
):
    mapping = TimeWindowPartitionMapping()

    if error_expected:
        with pytest.raises(DagsterInvalidInvocationError, match="invalid time windows"):
            mapping.get_upstream_partitions_for_partitions(
                subset_with_keys(downstream_partitions_def, downstream_keys),
                upstream_partitions_def,
                current_time=current_time,
            )

    else:
        assert (
            mapping.get_upstream_partitions_for_partitions(
                subset_with_keys(downstream_partitions_def, downstream_keys),
                upstream_partitions_def,
                current_time=current_time,
            ).get_partition_keys()
            == expected_upstream_keys
        )


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
            ["2022-01-02", "2022-01-09"],  # 2022-01-02 is Sunday, weekly cron starts from Sunday
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
        start=pendulum.instance(datetime.strptime(first_partition_window[0], fmt), tz="UTC"),
        end=pendulum.instance(datetime.strptime(first_partition_window[1], fmt), tz="UTC"),
    )

    last_partition_window_ = TimeWindow(
        start=pendulum.instance(datetime.strptime(last_partition_window[0], fmt), tz="UTC"),
        end=pendulum.instance(datetime.strptime(last_partition_window[1], fmt), tz="UTC"),
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
    # get_partition_keys
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
