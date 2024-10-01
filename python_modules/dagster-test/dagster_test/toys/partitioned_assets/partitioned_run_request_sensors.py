import random

from dagster import AssetSelection, RunRequest, SensorResult, define_asset_job, sensor

from dagster_test.toys.partitioned_assets.dynamic_asset_partitions import (
    ints_dynamic_asset,
    ints_dynamic_partitions_def,
)
from dagster_test.toys.partitioned_assets.hourly_and_daily_and_unpartitioned import (
    upstream_daily_partitioned_asset,
)


@sensor(asset_selection=AssetSelection.assets(ints_dynamic_asset))
def ints_dynamic_partitions_asset_selection_sensor(context):
    new_partition_key = str(random.randint(0, 100))
    return SensorResult(
        run_requests=[RunRequest(partition_key=new_partition_key)],
        dynamic_partitions_requests=[
            ints_dynamic_partitions_def.build_add_request([new_partition_key]),
            ints_dynamic_partitions_def.build_add_request([new_partition_key * 2]),
            ints_dynamic_partitions_def.build_add_request([new_partition_key * 3]),
        ],
    )


@sensor(
    job=define_asset_job(
        "ints_dynamic_partitions_job",
        AssetSelection.assets(ints_dynamic_asset),
        partitions_def=ints_dynamic_partitions_def,
    )
)
def ints_dynamic_partitions_job_sensor():
    new_partition_key = str(random.randint(0, 100))
    return SensorResult(
        run_requests=[
            RunRequest(partition_key=new_partition_key),
        ],
        dynamic_partitions_requests=[
            ints_dynamic_partitions_def.build_add_request([new_partition_key]),
            ints_dynamic_partitions_def.build_add_request([new_partition_key * 2]),
            ints_dynamic_partitions_def.build_add_request([new_partition_key * 3]),
        ],
    )


@sensor(asset_selection=AssetSelection.assets(upstream_daily_partitioned_asset))
def upstream_daily_partitioned_asset_sensor(context):
    latest_partition = upstream_daily_partitioned_asset.partitions_def.get_partition_keys()[-1]
    yield RunRequest(partition_key=latest_partition)
    yield define_asset_job(
        "upstream_daily_partitioned_asset_job",
        AssetSelection.assets(upstream_daily_partitioned_asset),
        partitions_def=upstream_daily_partitioned_asset.partitions_def,
    ).run_request_for_partition(latest_partition)
