import random

from dagster import (
    DailyPartitionsDefinition,
    MaterializeResult,
    asset,
    build_schedule_from_partitioned_job,
    define_asset_job,
)


@asset(partitions_def=DailyPartitionsDefinition(start_date="2023-10-01"))
def my_daily_partitioned_asset() -> MaterializeResult:
    some_metadata_value = random.randint(0, 100)

    return MaterializeResult(metadata={"foo": some_metadata_value})


partitioned_asset_job = define_asset_job("partitioned_job", selection=[my_daily_partitioned_asset])


my_partitioned_schedule = build_schedule_from_partitioned_job(
    partitioned_asset_job,
)
