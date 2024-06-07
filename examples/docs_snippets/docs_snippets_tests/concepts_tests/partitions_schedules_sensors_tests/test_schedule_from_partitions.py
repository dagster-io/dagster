from dagster import Definitions
from docs_snippets.concepts.partitions_schedules_sensors.schedule_from_partitions import (
    daily_asset,
    partitioned_asset_job,
    partitioned_asset_schedule,
)


def test_build_schedule_from_partitioned_job():
    Definitions(assets=[daily_asset], schedules=[partitioned_asset_schedule])
