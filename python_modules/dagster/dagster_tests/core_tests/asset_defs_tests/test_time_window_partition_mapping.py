import pendulum
import pytest
from dagster import (
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
    MonthlyPartitionsDefinition,
)
from dagster.core.asset_defs.asset_partitions import PartitionKeyRange
from dagster.core.asset_defs.time_window_partition_mapping import (
    TimeWindowPartitionMapping,
    round_datetime_to_period,
)
from dagster.core.definitions.partition import ScheduleType


def test_get_parent_partitions_same_partitioning():
    child_partitions_def = DailyPartitionsDefinition(start_date="2021-05-05")
    parent_partitions_def = DailyPartitionsDefinition(start_date="2021-05-05")
    # single partition key
    partition_key_range = PartitionKeyRange("2021-05-07", "2021-05-07")
    result = TimeWindowPartitionMapping().get_parent_partitions(
        child_partitions_def, parent_partitions_def, partition_key_range
    )
    assert partition_key_range == result

    # range of partition keys
    partition_key_range = PartitionKeyRange("2021-05-07", "2021-05-09")
    result = TimeWindowPartitionMapping().get_parent_partitions(
        child_partitions_def, parent_partitions_def, partition_key_range
    )
    assert partition_key_range == result


def test_get_parent_partitions_same_partitioning_different_formats():
    child_partitions_def = DailyPartitionsDefinition(start_date="2021-05-05")
    parent_partitions_def = DailyPartitionsDefinition(start_date="2021/05/05", fmt="%Y/%m/%d")

    result = TimeWindowPartitionMapping().get_parent_partitions(
        child_partitions_def, parent_partitions_def, PartitionKeyRange("2021-05-07", "2021-05-09")
    )
    assert result == PartitionKeyRange("2021/05/07", "2021/05/09")


def test_get_parent_partitions_hourly_child_daily_parent():
    child_partitions_def = HourlyPartitionsDefinition(start_date="2021-05-05-00:00")
    parent_partitions_def = DailyPartitionsDefinition(start_date="2021-05-05")
    result = TimeWindowPartitionMapping().get_parent_partitions(
        child_partitions_def,
        parent_partitions_def,
        PartitionKeyRange("2021-05-07-05:00", "2021-05-07-05:00"),
    )
    assert result == PartitionKeyRange("2021-05-07", "2021-05-07")

    result = TimeWindowPartitionMapping().get_parent_partitions(
        child_partitions_def,
        parent_partitions_def,
        PartitionKeyRange("2021-05-07-05:00", "2021-05-09-09:00"),
    )
    assert result == PartitionKeyRange("2021-05-07", "2021-05-09")


def test_get_parent_partitions_daily_child_hourly_parent():
    child_partitions_def = DailyPartitionsDefinition(start_date="2021-05-05")
    parent_partitions_def = HourlyPartitionsDefinition(start_date="2021-05-05-00:00")
    result = TimeWindowPartitionMapping().get_parent_partitions(
        child_partitions_def,
        parent_partitions_def,
        PartitionKeyRange("2021-05-07", "2021-05-07"),
    )
    assert result == PartitionKeyRange("2021-05-07-00:00", "2021-05-07-23:00")

    result = TimeWindowPartitionMapping().get_parent_partitions(
        child_partitions_def,
        parent_partitions_def,
        PartitionKeyRange("2021-05-07", "2021-05-09"),
    )
    assert result == PartitionKeyRange("2021-05-07-00:00", "2021-05-09-23:00")


def test_get_parent_partitions_monthly_child_daily_parent():
    child_partitions_def = MonthlyPartitionsDefinition(start_date="2021-05-01")
    parent_partitions_def = DailyPartitionsDefinition(start_date="2021-05-01")
    result = TimeWindowPartitionMapping().get_parent_partitions(
        child_partitions_def,
        parent_partitions_def,
        PartitionKeyRange("2021-05-01", "2021-07-01"),
    )
    assert result == PartitionKeyRange("2021-05-01", "2021-07-31")


@pytest.mark.parametrize(
    "dt_str, period, expected_str",
    [
        ("2020-01-01", ScheduleType.DAILY, "2020-01-01"),
        ("2020-01-01 01:00:00", ScheduleType.DAILY, "2020-01-01"),
        ("2020-01-01 01:00:00", ScheduleType.HOURLY, "2020-01-01 01:00:00"),
        ("2020-01-01", ScheduleType.MONTHLY, "2020-01-01"),
        ("2020-01-02", ScheduleType.MONTHLY, "2020-01-01"),
        ("2020-01-02 01:00:00", ScheduleType.MONTHLY, "2020-01-01"),
        ("2021-12-03", ScheduleType.WEEKLY, "2021-11-29"),
        ("2021-12-03  01:00:00", ScheduleType.WEEKLY, "2021-11-29"),
        ("2021-11-29", ScheduleType.WEEKLY, "2021-11-29"),
    ],
)
def test_round_datetime_to_period(dt_str, period, expected_str):
    dt = pendulum.parse(dt_str)
    expected_dt = pendulum.parse(expected_str)
    assert round_datetime_to_period(dt, period) == expected_dt
