from datetime import datetime

from dagster import (
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
    MonthlyPartitionsDefinition,
    TimeWindowPartitionMapping,
    TimeWindowPartitionsDefinition,
    WeeklyPartitionsDefinition,
)
from dagster._core.definitions.partition_key_range import PartitionKeyRange


def subset_with_key(partitions_def: TimeWindowPartitionsDefinition, key: str):
    return partitions_def.empty_subset().with_partition_keys([key])


def subset_with_key_range(partitions_def: TimeWindowPartitionsDefinition, start: str, end: str):
    return partitions_def.empty_subset().with_partition_keys(
        partitions_def.get_partition_keys_in_range(PartitionKeyRange(start, end))
    )


def test_get_upstream_partitions_for_partition_range_same_partitioning():
    downstream_partitions_def = DailyPartitionsDefinition(start_date="2021-05-05")
    upstream_partitions_def = DailyPartitionsDefinition(start_date="2021-05-05")
    # single partition key
    result = TimeWindowPartitionMapping().get_upstream_partitions_for_partitions(
        subset_with_key(downstream_partitions_def, "2021-05-07"),
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
        subset_with_key(downstream_partitions_def, "2021-05-07-05:00"),
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
        subset_with_key(downstream_partitions_def, "2021-05-07"),
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
        subset_with_key(downstream_partitions_def, "2021-05-07"), upstream_partitions_def
    ).get_partition_keys() == ["2021-05-06"]

    assert mapping.get_downstream_partitions_for_partitions(
        subset_with_key(upstream_partitions_def, "2021-05-06"), downstream_partitions_def
    ).get_partition_keys() == ["2021-05-07"]

    # first partition key
    assert (
        mapping.get_upstream_partitions_for_partitions(
            subset_with_key(downstream_partitions_def, "2021-05-05"), upstream_partitions_def
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
