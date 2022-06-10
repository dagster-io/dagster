from dagster import define_asset_job
from docs_snippets.concepts.partitions_schedules_sensors.partitioned_asset import (
    my_daily_partitioned_asset,
)


def test_partitioned_asset():
    my_job = define_asset_job("a").resolve([my_daily_partitioned_asset], [])
    assert my_job.execute_in_process(partition_key="2022-01-01").success
