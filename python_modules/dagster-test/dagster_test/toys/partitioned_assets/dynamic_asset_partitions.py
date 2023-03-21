import click
from dagster import (
    AssetSelection,
    DagsterInstance,
    DailyPartitionsDefinition,
    Definitions,
    DynamicPartitionsDefinition,
    MultiPartitionsDefinition,
    asset,
    define_asset_job,
    load_assets_from_current_module,
)

customers_partitions_def = DynamicPartitionsDefinition(name="customers")


@asset(partitions_def=customers_partitions_def, group_name="dynamic_asset_partitions")
def dynamic_partitions_asset1():
    ...


@asset(partitions_def=customers_partitions_def, group_name="dynamic_asset_partitions")
def dynamic_partitions_asset2(dynamic_partitions_asset1):
    ...


dynamic_partitions_job = define_asset_job(
    "dynamic_partitions_job",
    selection=AssetSelection.groups("dynamic_asset_partitions"),
    partitions_def=customers_partitions_def,
)

multipartition_w_dynamic_partitions_def = MultiPartitionsDefinition(
    {"customers": customers_partitions_def, "daily": DailyPartitionsDefinition("2023-01-01")}
)


@asset(
    partitions_def=multipartition_w_dynamic_partitions_def,
)
def dynamic_dimension_success():
    return 1


defs = Definitions(assets=load_assets_from_current_module(), jobs=[dynamic_partitions_job])


@click.command()
@click.option("--num-partitions", type=int)
def add_partitions(num_partitions):
    with DagsterInstance.get() as instance:
        partition_keys = [f"customer_{i}" for i in range(num_partitions)]
        instance.add_dynamic_partitions(customers_partitions_def.name, partition_keys)


if __name__ == "__main__":
    add_partitions()
