from datetime import datetime

from dagster import (
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
    MonthlyPartitionsDefinition,
    TimeWindowPartitionsDefinition,
)
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.time_window_partition_mapping import TimeWindowPartitionMapping


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


def test_get_upstream_partitions_for_partition_range_twice_daily_downstream_daily_upstream():
    start = datetime(year=2020, month=1, day=5)
    downstream_partitions_def = TimeWindowPartitionsDefinition(
        cron_schedule="0 0 * * *", start=start, fmt="%Y-%m-%d"
    )
    upstream_partitions_def = TimeWindowPartitionsDefinition(
        cron_schedule="0 0,11 * * *", start=start, fmt="%Y-%m-%d %H:%M"
    )
    result = TimeWindowPartitionMapping().get_upstream_partitions_for_partition_range(
        PartitionKeyRange("2021-05-01", "2021-05-03"),
        downstream_partitions_def,
        upstream_partitions_def,
    )
    assert result == PartitionKeyRange("2021-05-01 00:00", "2021-05-03 11:00")


def test_get_upstream_partitions_for_partition_range_daily_downstream_twice_daily_upstream():
    start = datetime(year=2020, month=1, day=5)
    downstream_partitions_def = TimeWindowPartitionsDefinition(
        cron_schedule="0 0,11 * * *", start=start, fmt="%Y-%m-%d %H:%M"
    )
    upstream_partitions_def = TimeWindowPartitionsDefinition(
        cron_schedule="0 0 * * *", start=start, fmt="%Y-%m-%d"
    )
    result = TimeWindowPartitionMapping().get_upstream_partitions_for_partition_range(
        PartitionKeyRange("2021-05-01 00:00", "2021-05-03 00:00"),
        downstream_partitions_def,
        upstream_partitions_def,
    )
    assert result == PartitionKeyRange("2021-05-01", "2021-05-03")


def test_get_upstream_partitions_for_partition_range_daily_non_aligned():
    start = datetime(year=2020, month=1, day=5)
    downstream_partitions_def = TimeWindowPartitionsDefinition(
        cron_schedule="0 0 * * *", start=start, fmt="%Y-%m-%d"
    )
    upstream_partitions_def = TimeWindowPartitionsDefinition(
        cron_schedule="0 11 * * *", start=start, fmt="%Y-%m-%d"
    )
    result = TimeWindowPartitionMapping().get_upstream_partitions_for_partition_range(
        PartitionKeyRange("2021-05-02", "2021-05-04"),
        downstream_partitions_def,
        upstream_partitions_def,
    )
    assert result == PartitionKeyRange("2021-05-01", "2021-05-04")
