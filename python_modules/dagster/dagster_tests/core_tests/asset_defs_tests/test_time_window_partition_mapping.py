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


def test_get_upstream_partitions_for_partition_range_same_partitioning():
    downstream_partitions_def = DailyPartitionsDefinition(start_date="2021-05-05")
    upstream_partitions_def = DailyPartitionsDefinition(start_date="2021-05-05")
    # single partition key
    partition_key_range = PartitionKeyRange("2021-05-07", "2021-05-07")
    result = TimeWindowPartitionMapping().get_upstream_partitions_for_partition_range(
        partition_key_range,
        downstream_partitions_def,
        upstream_partitions_def,
    )
    assert partition_key_range == result

    # range of partition keys
    partition_key_range = PartitionKeyRange("2021-05-07", "2021-05-09")
    result = TimeWindowPartitionMapping().get_upstream_partitions_for_partition_range(
        partition_key_range,
        downstream_partitions_def,
        upstream_partitions_def,
    )
    assert partition_key_range == result


def test_get_upstream_partitions_for_partition_range_same_partitioning_different_formats():
    downstream_partitions_def = DailyPartitionsDefinition(start_date="2021-05-05")
    upstream_partitions_def = DailyPartitionsDefinition(start_date="2021/05/05", fmt="%Y/%m/%d")

    result = TimeWindowPartitionMapping().get_upstream_partitions_for_partition_range(
        PartitionKeyRange("2021-05-07", "2021-05-09"),
        downstream_partitions_def,
        upstream_partitions_def,
    )
    assert result == PartitionKeyRange("2021/05/07", "2021/05/09")


def test_get_upstream_partitions_for_partition_range_hourly_downstream_daily_upstream():
    downstream_partitions_def = HourlyPartitionsDefinition(start_date="2021-05-05-00:00")
    upstream_partitions_def = DailyPartitionsDefinition(start_date="2021-05-05")
    result = TimeWindowPartitionMapping().get_upstream_partitions_for_partition_range(
        PartitionKeyRange("2021-05-07-05:00", "2021-05-07-05:00"),
        downstream_partitions_def,
        upstream_partitions_def,
    )
    assert result == PartitionKeyRange("2021-05-07", "2021-05-07")

    result = TimeWindowPartitionMapping().get_upstream_partitions_for_partition_range(
        PartitionKeyRange("2021-05-07-05:00", "2021-05-09-09:00"),
        downstream_partitions_def,
        upstream_partitions_def,
    )
    assert result == PartitionKeyRange("2021-05-07", "2021-05-09")


def test_get_upstream_partitions_for_partition_range_daily_downstream_hourly_upstream():
    downstream_partitions_def = DailyPartitionsDefinition(start_date="2021-05-05")
    upstream_partitions_def = HourlyPartitionsDefinition(start_date="2021-05-05-00:00")
    result = TimeWindowPartitionMapping().get_upstream_partitions_for_partition_range(
        PartitionKeyRange("2021-05-07", "2021-05-07"),
        downstream_partitions_def,
        upstream_partitions_def,
    )
    assert result == PartitionKeyRange("2021-05-07-00:00", "2021-05-07-23:00")

    result = TimeWindowPartitionMapping().get_upstream_partitions_for_partition_range(
        PartitionKeyRange("2021-05-07", "2021-05-09"),
        downstream_partitions_def,
        upstream_partitions_def,
    )
    assert result == PartitionKeyRange("2021-05-07-00:00", "2021-05-09-23:00")


def test_get_upstream_partitions_for_partition_range_monthly_downstream_daily_upstream():
    downstream_partitions_def = MonthlyPartitionsDefinition(start_date="2021-05-01")
    upstream_partitions_def = DailyPartitionsDefinition(start_date="2021-05-01")
    result = TimeWindowPartitionMapping().get_upstream_partitions_for_partition_range(
        PartitionKeyRange("2021-05-01", "2021-07-01"),
        downstream_partitions_def,
        upstream_partitions_def,
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
        ("2021-12-03 01:00:00", ScheduleType.WEEKLY, "2021-11-29"),
        ("2021-11-29", ScheduleType.WEEKLY, "2021-11-29"),
    ],
)
def test_round_datetime_to_period(dt_str, period, expected_str):
    dt = pendulum.parse(dt_str)
    expected_dt = pendulum.parse(expected_str)
    assert round_datetime_to_period(dt, period) == expected_dt
