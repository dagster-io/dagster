from dagster import materialize
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
)
from docs_snippets.concepts.partitions_schedules_sensors.backfills.single_run_backfill_io_manager import (
    MyIOManager,
    daily_partition,
    events,
    raw_events,
)


def test_io_manager():
    assert materialize(
        [events, raw_events],
        tags={
            ASSET_PARTITION_RANGE_START_TAG: "2020-01-02",
            ASSET_PARTITION_RANGE_END_TAG: "2020-01-04",
        },
        resources={"io_manager": MyIOManager()},
    ).success
