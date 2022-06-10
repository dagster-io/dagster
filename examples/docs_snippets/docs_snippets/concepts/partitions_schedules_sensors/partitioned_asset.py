from dagster import DailyPartitionsDefinition, asset


@asset(partitions_def=DailyPartitionsDefinition(start_date="2022-01-01"))
def my_daily_partitioned_asset(context):
    context.log.info(
        f"Processing asset partition '{context.asset_partition_key_for_output()}'"
    )
