from dagster import (
    asset,
    AssetKey,
    build_input_context,
    build_output_context,
    materialize,
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
)
from pytest import fixture
import datetime


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
    def daily_asset(hourly_asset):
        return hourly_asset

    # Build hourly materializations
    for hour in range(0, 24):
        materialize(
            [hourly_asset],
            partition_key=f"2022-01-01-{hour:02d}:00",
        )

    # Materialize daily asset that depends on hourlies
    result = materialize(
        [*hourly_asset.to_source_assets(), daily_asset],
        partition_key="2022-01-01",
    )
    assert result.output_for_node("daily_asset") == 24 * [42]
