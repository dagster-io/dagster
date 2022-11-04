import datetime

from pytest import fixture

from dagster import DailyPartitionsDefinition, HourlyPartitionsDefinition, asset, materialize


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
    hourly_keys = [f"2022-01-01-{hour:02d}:00" for hour in range(0, 24)]
    for key in hourly_keys:
        materialize(
            [hourly_asset],
            partition_key=key,
        )

    # Materialize daily asset that depends on hourlies
    result = materialize(
        [*hourly_asset.to_source_assets(), daily_asset],
        partition_key="2022-01-01",
    )
    expected = {k: 42 for k in hourly_keys}
    assert result.output_for_node("daily_asset") == expected


def test_partitioned_io_manager_preserves_single_partition_dependency(daily):
    @asset(partitions_def=daily)
    def upstream_asset():
        return 42

    @asset(partitions_def=daily)
    def daily_asset(upstream_asset):
        return upstream_asset

    result = materialize(
        [upstream_asset, daily_asset],
        partition_key="2022-01-01",
    )
    assert result.output_for_node("daily_asset") == 42
