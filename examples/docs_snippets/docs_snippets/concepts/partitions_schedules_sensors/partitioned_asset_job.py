from dagster import (
    AssetSelection,
    HourlyPartitionsDefinition,
    asset,
    define_asset_job,
    repository,
)

hourly_partitions_def = HourlyPartitionsDefinition(start_date="2022-05-31-00:00")


@asset(partitions_def=hourly_partitions_def)
def asset1():
    ...


@asset(partitions_def=hourly_partitions_def)
def asset2():
    ...


partitioned_asset_job = define_asset_job(
    name="asset_1_and_2_job",
    selection=AssetSelection.assets(asset1, asset2),
    partitions_def=hourly_partitions_def,
)


@repository
def repo():
    return [asset1, asset2, partitioned_asset_job]
