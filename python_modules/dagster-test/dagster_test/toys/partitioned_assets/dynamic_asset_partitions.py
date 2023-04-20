import random

import click
from dagster import (
    AssetKey,
    AssetSelection,
    DagsterInstance,
    DailyPartitionsDefinition,
    DynamicPartitionsDefinition,
    MultiPartitionsDefinition,
    RunRequest,
    SensorResult,
    asset,
    define_asset_job,
    sensor,
)

customers_partitions_def = DynamicPartitionsDefinition(name="customers")


@asset(partitions_def=customers_partitions_def, group_name="dynamic_asset_partitions")
def dynamic_partitions_asset1():
    ...


@asset(partitions_def=customers_partitions_def, group_name="dynamic_asset_partitions")
def dynamic_partitions_asset2(dynamic_partitions_asset1):
    ...


multipartition_w_dynamic_partitions_def = MultiPartitionsDefinition(
    {"customers": customers_partitions_def, "daily": DailyPartitionsDefinition("2023-01-01")}
)


@asset(
    partitions_def=multipartition_w_dynamic_partitions_def,
    group_name="dynamic_asset_partitions",
)
def multipartitioned_with_dynamic_dimension():
    return 1


ints_dynamic_partitions_def = DynamicPartitionsDefinition(name="ints")


@asset(partitions_def=ints_dynamic_partitions_def, group_name="dynamic_asset_partitions")
def ints_dynamic_asset():
    return 1


@sensor(
    job=define_asset_job(
        "ints_job",
        AssetSelection.assets(ints_dynamic_asset),
        partitions_def=ints_dynamic_partitions_def,
    )
)
def ints_job_sensor():
    new_partition_key = str(random.randint(0, 100))
    return SensorResult(
        run_requests=[
            RunRequest(partition_key=new_partition_key),
        ],
        dynamic_partitions_requests=[
            ints_dynamic_partitions_def.build_add_request([new_partition_key])
        ],
    )


dynamic_partitions_job = define_asset_job(
    "dynamic_partitions_job",
    selection=AssetSelection.keys(
        AssetKey("dynamic_partitions_asset1"), AssetKey("dynamic_partitions_asset2")
    ),
    partitions_def=customers_partitions_def,
)


@sensor(asset_selection=AssetSelection.assets(ints_dynamic_asset))
def ints_asset_selection_sensor(context):
    new_partition_key = str(random.randint(0, 100))
    return SensorResult(
        run_requests=[RunRequest(partition_key=new_partition_key)],
        dynamic_partitions_requests=[
            ints_dynamic_partitions_def.build_add_request([new_partition_key])
        ],
    )


@click.command()
@click.option("--num-partitions", type=int)
def add_partitions(num_partitions):
    with DagsterInstance.get() as instance:
        partition_keys = [f"customer_{i}" for i in range(num_partitions)]
        instance.add_dynamic_partitions(customers_partitions_def.name, partition_keys)


if __name__ == "__main__":
    add_partitions()
