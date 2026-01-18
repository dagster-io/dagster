import dagster as dg

hourly_partitions_def = dg.HourlyPartitionsDefinition(start_date="2022-05-31-00:00")


@dg.asset(partitions_def=hourly_partitions_def)
def asset1(): ...


@dg.asset(partitions_def=hourly_partitions_def)
def asset2(): ...


partitioned_asset_job = dg.define_asset_job(
    name="asset_1_and_2_job",
    selection=dg.AssetSelection.assets(asset1, asset2),
    partitions_def=hourly_partitions_def,
)


defs = dg.Definitions(
    assets=[asset1, asset2],
    jobs=[partitioned_asset_job],
)
