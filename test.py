from dagster import AssetExecutionContext, BackfillPolicy, DailyPartitionsDefinition, asset


@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"),
    backfill_policy=BackfillPolicy.single_run(),
)
def events(context: AssetExecutionContext) -> None:
    start_datetime, end_datetime = context.partition_time_window

    context.log.info(f"Materializing partitions for {start_datetime} to {end_datetime}")
