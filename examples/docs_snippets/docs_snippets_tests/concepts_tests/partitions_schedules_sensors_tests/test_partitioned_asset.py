from dagster import AssetGroup
from docs_snippets.concepts.partitions_schedules_sensors.partitioned_asset import (
    my_daily_partitioned_asset,
)


def test_partitioned_asset():
    assert (
        AssetGroup([my_daily_partitioned_asset])
        .build_job("a")
        .execute_in_process(partition_key="2022-01-01")
        .success
    )
