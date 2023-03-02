from dagster import (
    AssetSelection,
    Definitions,
    DynamicPartitionsDefinition,
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


defs = Definitions(assets=load_assets_from_current_module(), jobs=[dynamic_partitions_job])
