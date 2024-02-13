import click
from dagster import (
    AssetSelection,
    DagsterInstance,
    DailyPartitionsDefinition,
    DynamicPartitionsDefinition,
    MultiPartitionsDefinition,
    asset,
    define_asset_job,
)

customers_partitions_def = DynamicPartitionsDefinition(name="customers")


@asset(partitions_def=customers_partitions_def, group_name="dynamic_asset_partitions")
def customers_dynamic_partitions_asset1():
    ...


@asset(partitions_def=customers_partitions_def, group_name="dynamic_asset_partitions")
def customers_dynamic_partitions_asset2(customers_dynamic_partitions_asset1):
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


customers_dynamic_partitions_job = define_asset_job(
    "customers_dynamic_partitions_job",
    selection=AssetSelection.assets(
        customers_dynamic_partitions_asset1, customers_dynamic_partitions_asset2
    ),
    partitions_def=customers_partitions_def,
)


@click.command()
@click.option("--num-partitions", type=int)
def add_partitions(num_partitions):
    with DagsterInstance.get() as instance:
        partition_keys = [f"customer_{i}" for i in range(num_partitions)]
        instance.add_dynamic_partitions(customers_partitions_def.name, partition_keys)


if __name__ == "__main__":
    add_partitions()
