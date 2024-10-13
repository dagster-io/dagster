from dagster import BackfillPolicy, DailyPartitionsDefinition, MaterializeResult, asset


@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2023-01-01"),
    backfill_policy=BackfillPolicy.single_run(),
    group_name="with_backfill_policy",
)
def successful_single_run_backfill_policy() -> MaterializeResult:
    return MaterializeResult()


@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2023-01-01"),
    backfill_policy=BackfillPolicy.single_run(),
    group_name="with_backfill_policy",
)
def failure_single_run_backfill_policy() -> None:
    raise Exception("This asset failed")
