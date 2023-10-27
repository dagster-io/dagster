from dagster import (
    SourceAsset,
    materialize,
    mem_io_manager,
)
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
)
from docs_snippets.concepts.partitions_schedules_sensors.backfills.single_run_backfill_asset import (
    events,
)


def test_asset():
    raw_events = SourceAsset("raw_events", partitions_def=events.partitions_def)

    assert materialize(
        [raw_events, events],
        tags={
            ASSET_PARTITION_RANGE_START_TAG: "2020-01-02",
            ASSET_PARTITION_RANGE_END_TAG: "2020-01-04",
        },
        resources={"io_manager": mem_io_manager},
    ).success
