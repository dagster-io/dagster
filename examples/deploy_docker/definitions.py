import dagster as dg


@dg.asset(
    op_tags={"operation": "example"},
    partitions_def=dg.DailyPartitionsDefinition("2024-01-01"),
)
def example_asset(context: dg.AssetExecutionContext):
    context.log.info(context.partition_key)


partitioned_asset_job = dg.define_asset_job("partitioned_job", selection=[example_asset])

defs = dg.Definitions(assets=[example_asset], jobs=[partitioned_asset_job])
