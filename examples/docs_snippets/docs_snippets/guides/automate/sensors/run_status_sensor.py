# start_assets
import json
from datetime import datetime, timedelta

import dagster as dg


@dg.asset
def first_asset(context: dg.AssetExecutionContext) -> None:
    context.log.info("First asset")


@dg.asset
def second_asset(context: dg.AssetExecutionContext) -> None:
    context.log.info("Second asset")


@dg.asset
def third_asset(context: dg.AssetExecutionContext) -> None:
    context.log.info("Third asset")


# Define the upstream jobs
upstream_job_1 = dg.define_asset_job(name="upstream_job_1", selection="first_asset")

upstream_job_2 = dg.define_asset_job(name="upstream_job_2", selection="second_asset")

downstream_job = dg.define_asset_job(name="downstream_job", selection="third_asset")

# end_assets


# start_sensors
import json
from datetime import datetime, timedelta

import dagster as dg

# Define the job names for the upstream jobs
UPSTREAM_JOB_A = "upstream_job_1"
UPSTREAM_JOB_B = "upstream_job_2"

# Define the downstream job
DOWNSTREAM_JOB = "downstream_job"


@dg.sensor(job_name=DOWNSTREAM_JOB)
def compare_completion_times_sensor(context: dg.SensorEvaluationContext):
    instance = context.instance
    now = datetime.now()
    one_day_ago = now - timedelta(days=1)

    filter_a = dg.RunsFilter(
        job_name=UPSTREAM_JOB_A, statuses=[dg.DagsterRunStatus.SUCCESS]
    )
    filter_b = dg.RunsFilter(
        job_name=UPSTREAM_JOB_B, statuses=[dg.DagsterRunStatus.SUCCESS]
    )

    run_records_a = instance.get_run_records(
        filters=filter_a, limit=1, order_by="update_timestamp", ascending=False
    )
    run_records_b = instance.get_run_records(
        filters=filter_b, limit=1, order_by="update_timestamp", ascending=False
    )
    if not run_records_a or not run_records_b:
        return dg.SkipReason(
            "One or both upstream jobs have not completed successfully."
        )

    completion_time_a = run_records_a[0].end_time
    completion_time_b = run_records_b[0].end_time

    previous_cursor = json.loads(context.cursor) if context.cursor else {}
    previous_completion_time_a = previous_cursor.get("completion_time_a")
    previous_completion_time_b = previous_cursor.get("completion_time_b")

    if isinstance(previous_completion_time_a, float):
        previous_completion_time_a = datetime.fromtimestamp(previous_completion_time_a)
    if isinstance(previous_completion_time_b, float):
        previous_completion_time_b = datetime.fromtimestamp(previous_completion_time_b)

    completion_time_a = (
        datetime.fromtimestamp(completion_time_a)
        if completion_time_a is not None
        else None
    )
    completion_time_b = (
        datetime.fromtimestamp(completion_time_b)
        if completion_time_b is not None
        else None
    )

    if (
        completion_time_a
        and completion_time_b
        and completion_time_a > one_day_ago
        and completion_time_b > one_day_ago
        and (
            not previous_completion_time_a
            or completion_time_a > previous_completion_time_a
        )
        and (
            not previous_completion_time_b
            or completion_time_b > previous_completion_time_b
        )
    ):
        new_cursor = json.dumps(
            {
                "completion_time_a": completion_time_a.timestamp(),
                "completion_time_b": completion_time_b.timestamp(),
            }
        )
        context.update_cursor(new_cursor)

        return dg.RunRequest(run_key=None, run_config={})
    else:
        return dg.SkipReason(
            "One or both upstream jobs did not complete within the past day."
        )


# end_sensors
