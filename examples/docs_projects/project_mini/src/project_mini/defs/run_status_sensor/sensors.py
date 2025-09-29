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

    # start_runs_filter
    filter_a = dg.RunsFilter(job_name=UPSTREAM_JOB_A, statuses=[dg.DagsterRunStatus.SUCCESS])
    filter_b = dg.RunsFilter(job_name=UPSTREAM_JOB_B, statuses=[dg.DagsterRunStatus.SUCCESS])

    # end_runs_filter

    run_records_a = instance.get_run_records(
        filters=filter_a, limit=1, order_by="update_timestamp", ascending=False
    )
    run_records_b = instance.get_run_records(
        filters=filter_b, limit=1, order_by="update_timestamp", ascending=False
    )
    if not run_records_a or not run_records_b:
        return dg.SkipReason("One or both upstream jobs have not completed successfully.")

    completion_time_a = run_records_a[0].end_time
    completion_time_b = run_records_b[0].end_time

    # start_cursor_tracking
    previous_cursor = json.loads(context.cursor) if context.cursor else {}
    previous_completion_time_a = previous_cursor.get("completion_time_a")
    previous_completion_time_b = previous_cursor.get("completion_time_b")

    if isinstance(previous_completion_time_a, float):
        previous_completion_time_a = datetime.fromtimestamp(previous_completion_time_a)
    if isinstance(previous_completion_time_b, float):
        previous_completion_time_b = datetime.fromtimestamp(previous_completion_time_b)
    # end_cursor_tracking

    completion_time_a = datetime.fromtimestamp(completion_time_a)
    completion_time_b = datetime.fromtimestamp(completion_time_b)

    # start_conditional_trigger
    if (
        completion_time_a
        and completion_time_b
        and completion_time_a > one_day_ago
        and completion_time_b > one_day_ago
        and (not previous_completion_time_a or completion_time_a > previous_completion_time_a)
        and (not previous_completion_time_b or completion_time_b > previous_completion_time_b)
    ):
        # end_conditional_trigger
        new_cursor = json.dumps(
            {
                "completion_time_a": completion_time_a.timestamp(),
                "completion_time_b": completion_time_b.timestamp(),
            }
        )
        context.update_cursor(new_cursor)

        return dg.RunRequest(run_key=None, run_config={})
    else:
        return dg.SkipReason("One or both upstream jobs did not complete within the past day.")
