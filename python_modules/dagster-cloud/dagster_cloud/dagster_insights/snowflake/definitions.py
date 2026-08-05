import warnings
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import TYPE_CHECKING

from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetsDefinition,
    AssetSelection,
    HourlyPartitionsDefinition,
    RunRequest,
    ScheduleDefinition,
    ScheduleEvaluationContext,
    TimeWindow,
    asset,
    build_schedule_from_partitioned_job,
    define_asset_job,
    fs_io_manager,
    schedule,
)
from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
)

from dagster_cloud.dagster_insights.metrics_utils import put_cost_information
from dagster_cloud.dagster_insights.snowflake.dagster_snowflake_insights import (
    get_cost_data_for_hour,
)

if TYPE_CHECKING:
    from dagster_snowflake import SnowflakeConnection

SNOWFLAKE_QUERY_HISTORY_LATENCY_SLA_MINS = 45


@dataclass
class SnowflakeInsightsDefinitions:
    assets: Sequence[AssetsDefinition]
    schedule: ScheduleDefinition


def _build_run_request_for_partition_key_range(
    job: UnresolvedAssetJobDefinition,
    asset_keys: Sequence[AssetKey],
    partition_range_start: str,
    partition_range_end: str,
) -> RunRequest:
    tags = {
        ASSET_PARTITION_RANGE_START_TAG: partition_range_start,
        ASSET_PARTITION_RANGE_END_TAG: partition_range_end,
    }
    partition_key = partition_range_start if partition_range_start == partition_range_end else None
    return RunRequest(
        job_name=job.name, asset_selection=asset_keys, partition_key=partition_key, tags=tags
    )


def create_snowflake_insights_asset_and_schedule(
    start_date: datetime | date | str,
    name: str | None = None,
    group_name: str | None = None,
    job_name: str = "snowflake_insights_import",
    dry_run=False,
    allow_partial_partitions=True,
    snowflake_resource_key: str = "snowflake",
    snowflake_usage_latency: int = SNOWFLAKE_QUERY_HISTORY_LATENCY_SLA_MINS,
    partition_end_offset_hrs: int = 1,
    schedule_batch_size_hrs: int = 1,
    submit_to_s3_only: bool = True,  # DEPRECATED
) -> SnowflakeInsightsDefinitions:
    """Generates a pre-defined Dagster asset and schedule that can be used to import Snowflake cost
    data into Dagster Insights.

    The schedule will run hourly, and will query the Snowflake query_history table for all queries
    that ran in the hour starting at the scheduled time. It will then submit the cost data to
    Dagster Insights.

    Args:
        start_date (Union[datetime, str]): The date to start the partitioned schedule on. This should be the date
            that you began to track cost data alongside your dbt runs.
        name (Optional[str]): The name of the asset. Defaults to "snowflake_query_history".
        group_name (Optional[str]): The name of the asset group. Defaults to the default group.
        job_name (str): The name of the job that will be created to run the schedule. Defaults to
            "snowflake_insights_import".
        dry_run (bool): If true, the schedule will print the cost data to stdout instead of
            submitting it to Dagster Insights. Defaults to True.
        snowflake_resource_key (str): The name of the snowflake resource key to use. Defaults to
            "snowflake".
        partition_end_offset_hrs (int): The number of additional hours to wait before querying
            Snowflake for the latest data. This is useful in case the Snowflake query_history table
            is not immediately available. Defaults to 1
        schedule_batch_size_hrs (int): The number of hours of data to process in each schedule
            run. For example, if this is set to 2, the schedule will run every 2 hours and process
            2 hours of data. Defaults to 1.
    """
    # for backcompat, this used to take `date`
    if isinstance(start_date, date):
        start_date = start_date.strftime("%Y-%m-%d-%H:%M")

    if submit_to_s3_only is False:
        warnings.warn(
            "The `submit_to_s3_only` parameter is now deprecated. Insights cost data will now always be uploaded to Dagster Insights via S3."
        )

    partition_end_offset_hrs = -abs(partition_end_offset_hrs)

    partitions_def = HourlyPartitionsDefinition(
        start_date=start_date, end_offset=partition_end_offset_hrs
    )

    @asset(
        name=name,
        group_name=group_name,
        partitions_def=partitions_def,
        required_resource_keys={snowflake_resource_key},
        io_manager_def=fs_io_manager,
    )
    def poll_snowflake_query_history_hour(
        context: AssetExecutionContext,
    ) -> None:
        snowflake: SnowflakeConnection = getattr(context.resources, snowflake_resource_key)

        start_hour = context.partition_time_window.start
        end_hour = context.partition_time_window.end

        now = datetime.now().astimezone(timezone.utc)
        earliest_call_time = end_hour + timedelta(minutes=snowflake_usage_latency)
        if now < earliest_call_time:
            err = (
                "Attempted to gather Snowflake usage information before the Snowflake query_history table may be"
                f" available. For hour starting {start_hour.isoformat()} you can call it"
                f" starting at {earliest_call_time.isoformat()} (it is currently"
                f" {now.isoformat()})"
            )
            if allow_partial_partitions:
                context.log.error(err)
            else:
                raise RuntimeError(err)

        costs = (
            get_cost_data_for_hour(
                snowflake,
                start_hour,
                end_hour,
            )
            or []
        )
        snowflake_query_end_time = datetime.now().astimezone(timezone.utc)
        context.log.info(
            f"Fetched query history information from {start_hour.isoformat()} to {end_hour.isoformat()} in {(snowflake_query_end_time - now).total_seconds()} seconds"
        )

        if dry_run:
            pass
        else:
            context.log.info(
                f"Submitting cost information for {len(costs)} queries to Dagster Insights"
            )
            put_cost_information(
                context=context,
                metric_name="snowflake_credits",
                cost_information=costs,
                start=start_hour.timestamp(),
                end=end_hour.timestamp(),
            )

    insights_job = define_asset_job(
        job_name,
        AssetSelection.assets(poll_snowflake_query_history_hour),
        partitions_def=partitions_def,
    )

    if schedule_batch_size_hrs == 1:
        insights_schedule = build_schedule_from_partitioned_job(
            job=insights_job,
            minute_of_hour=59,
        )
    else:

        @schedule(
            job=insights_job,
            name=f"{job_name}_schedule_{schedule_batch_size_hrs}_hrs",
            cron_schedule=f"59 0/{schedule_batch_size_hrs} * * *",
        )
        def _insights_schedule(context: ScheduleEvaluationContext):
            timestamp = context.scheduled_execution_time.replace(
                minute=0, second=0, microsecond=0
            ) + timedelta(hours=partition_end_offset_hrs)
            n_hours_ago = timestamp - timedelta(hours=schedule_batch_size_hrs)
            window = TimeWindow(start=n_hours_ago, end=timestamp)

            partition_key_range = partitions_def.get_partition_key_range_for_time_window(window)

            yield _build_run_request_for_partition_key_range(
                insights_job,
                [poll_snowflake_query_history_hour.key],
                partition_key_range.start,
                partition_key_range.end,
            )

        insights_schedule = _insights_schedule

    # schedule may be a UnresolvedPartitionedAssetScheduleDefinition so we ignore the type check
    return SnowflakeInsightsDefinitions(
        assets=[poll_snowflake_query_history_hour],
        schedule=insights_schedule,  # type: ignore
    )
