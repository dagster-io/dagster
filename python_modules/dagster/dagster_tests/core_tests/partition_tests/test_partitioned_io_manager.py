import datetime
from typing import Any

import dagster as dg
import pytest
from pytest import fixture


@fixture
def start():
    return datetime.datetime(2022, 1, 1)


@fixture
def hourly(start):
    return dg.HourlyPartitionsDefinition(start_date=f"{start:%Y-%m-%d-%H:%M}")


@fixture
def daily(start):
    return dg.DailyPartitionsDefinition(start_date=f"{start:%Y-%m-%d}")


def test_partitioned_io_manager(hourly, daily):
    @dg.asset(partitions_def=hourly)
    def hourly_asset():
        return 42

    @dg.asset(partitions_def=daily)
    def daily_asset(hourly_asset: dict[str, Any]):
        return hourly_asset

    with dg.instance_for_test() as instance:
        # Build hourly materializations
        hourly_keys = [f"2022-01-01-{hour:02d}:00" for hour in range(0, 24)]
        for key in hourly_keys:
            dg.materialize(
                [hourly_asset],
                partition_key=key,
                instance=instance,
            )

        # Materialize daily asset that depends on hourlies
        result = dg.materialize(
            [*hourly_asset.to_source_assets(), daily_asset],
            partition_key="2022-01-01",
            instance=instance,
        )
        expected = {k: 42 for k in hourly_keys}
        assert result.output_for_node("daily_asset") == expected


def test_partitioned_io_manager_preserves_single_partition_dependency(daily):
    @dg.asset(partitions_def=daily)
    def upstream_asset():
        return 42

    @dg.asset(partitions_def=daily)
    def daily_asset(upstream_asset: int):
        return upstream_asset

    result = dg.materialize(
        [upstream_asset, daily_asset],
        partition_key="2022-01-01",
    )
    assert result.output_for_node("daily_asset") == 42


def test_partitioned_io_manager_single_partition_dependency_errors_with_wrong_typing(daily):
    @dg.asset(partitions_def=daily)
    def upstream_asset():
        return 42

    @dg.asset(partitions_def=daily)
    def daily_asset(upstream_asset: dict[str, Any]):
        return upstream_asset

    with pytest.raises(dg.DagsterTypeCheckDidNotPass):
        dg.materialize([upstream_asset, daily_asset], partition_key="2022-01-01")
