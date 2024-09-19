import datetime
from typing import Any, Dict

import pytest
from dagster import (
    DagsterTypeCheckDidNotPass,
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
    asset,
    materialize,
)
from dagster._core.instance_for_test import instance_for_test
from pytest import fixture


@fixture
def start():
    return datetime.datetime(2022, 1, 1)


@fixture
def hourly(start):
    return HourlyPartitionsDefinition(start_date=f"{start:%Y-%m-%d-%H:%M}")


@fixture
def daily(start):
    return DailyPartitionsDefinition(start_date=f"{start:%Y-%m-%d}")


def test_partitioned_io_manager(hourly, daily):
    @asset(partitions_def=hourly)
    def hourly_asset():
        return 42

    @asset(partitions_def=daily)
    def daily_asset(hourly_asset: Dict[str, Any]):
        return hourly_asset

    with instance_for_test() as instance:
        # Build hourly materializations
        hourly_keys = [f"2022-01-01-{hour:02d}:00" for hour in range(0, 24)]
        for key in hourly_keys:
            materialize(
                [hourly_asset],
                partition_key=key,
                instance=instance,
            )

        # Materialize daily asset that depends on hourlies
        result = materialize(
            [*hourly_asset.to_source_assets(), daily_asset],
            partition_key="2022-01-01",
            instance=instance,
        )
        expected = {k: 42 for k in hourly_keys}
        assert result.output_for_node("daily_asset") == expected


def test_partitioned_io_manager_preserves_single_partition_dependency(daily):
    @asset(partitions_def=daily)
    def upstream_asset():
        return 42

    @asset(partitions_def=daily)
    def daily_asset(upstream_asset: int):
        return upstream_asset

    result = materialize(
        [upstream_asset, daily_asset],
        partition_key="2022-01-01",
    )
    assert result.output_for_node("daily_asset") == 42


def test_partitioned_io_manager_single_partition_dependency_errors_with_wrong_typing(daily):
    @asset(partitions_def=daily)
    def upstream_asset():
        return 42

    @asset(partitions_def=daily)
    def daily_asset(upstream_asset: Dict[str, Any]):
        return upstream_asset

    with pytest.raises(DagsterTypeCheckDidNotPass):
        materialize([upstream_asset, daily_asset], partition_key="2022-01-01")
