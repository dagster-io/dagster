from datetime import datetime
from typing import Sequence, Optional

from dagster import (
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
    MonthlyPartitionsDefinition,
    TimeWindowPartitionMapping,
    TimeWindowPartitionsDefinition,
    WeeklyPartitionsDefinition,
)
import pytest
from dagster._core.definitions.partition_key_range import PartitionKeyRange


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
    "upstream_partitions_def,downstream_partitions_def,upstream_keys,downstream_keys,current_time",
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
            # When current time is not provided, returns all downstream partitions
            HourlyPartitionsDefinition(start_date="2021-05-05-00:00"),
            DailyPartitionsDefinition(start_date="2021-05-05"),
            ["2021-05-05-23:00", "2021-05-06-00:00", "2021-05-06-01:00"],
            ["2021-05-05", "2021-05-06"],
            None,
        ),
    ],
)
def test_get_downstream_with_current_time(
    upstream_partitions_def: TimeWindowPartitionsDefinition,
    downstream_partitions_def: TimeWindowPartitionsDefinition,
    upstream_keys: Sequence[str],
    downstream_keys: Sequence[str],
    current_time: Optional[datetime],
):
    mapping = TimeWindowPartitionMapping()
    assert (
        mapping.get_downstream_partitions_for_partitions(
            subset_with_keys(upstream_partitions_def, upstream_keys),
            downstream_partitions_def,
            current_time=current_time,
        ).get_partition_keys()
        == downstream_keys
    )


# TODO test current time with offsets
