from dagster import BackfillPolicy, DailyPartitionsDefinition, MaterializeResult, asset


@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2023-01-01"),
    backfill_policy=BackfillPolicy.single_run(),
    group_name="with_backfill_policy",
)
def successful_daily_asset() -> MaterializeResult:
    return MaterializeResult()


@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2023-01-01"),
    backfill_policy=BackfillPolicy.single_run(),
    group_name="with_backfill_policy",
)
def failing_daily_asset() -> None:
    raise Exception("This asset failed")
