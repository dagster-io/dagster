from dagster import DailyPartitionsDefinition, asset, materialize
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
)
from docs_snippets.concepts.partitions_schedules_sensors.backfills.single_run_backfill_io_manager import (
    MyIOManager,
)


def test_io_manager():
    daily = DailyPartitionsDefinition(start_date="2020-01-01")

    @asset(partitions_def=daily)
    def asset1():
        ...

    @asset(partitions_def=daily)
    def asset2(asset1):
        ...

    assert materialize(
        [asset1, asset2],
        tags={
            ASSET_PARTITION_RANGE_START_TAG: "2020-01-02",
            ASSET_PARTITION_RANGE_END_TAG: "2020-01-04",
        },
        resources={"io_manager": MyIOManager()},
    ).success
