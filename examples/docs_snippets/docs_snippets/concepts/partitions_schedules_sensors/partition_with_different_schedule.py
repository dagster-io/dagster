from datetime import timedelta

import dagster as dg

hourly_partition = dg.HourlyPartitionsDefinition(start_date="2023-01-21-00:00")


@dg.asset(
    partitions_def=hourly_partition,
)
def partition_asset(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    partition_key = context.partition_key
    return dg.MaterializeResult(metadata={"partition": partition_key})


@dg.schedule(
    job=dg.define_asset_job("hourly_partition_job", selection=[partition_asset]),
    cron_schedule="*/1 * * * *",
)
def every_minute_partition_schedule(context: dg.ScheduleEvaluationContext):
    """Schedule that runs the partition asset every minute with the appropriate hourly partition."""
    scheduled_date = context.scheduled_execution_time

    # Use the previous hour for the partition key
    previous_hour = scheduled_date - timedelta(hours=1)

    # Convert datetime to string format expected by hourly partition (YYYY-MM-DD-HH:00)
    partition_key = previous_hour.strftime("%Y-%m-%d-%H:00")

    return dg.RunRequest(
        partition_key=partition_key,
    )
