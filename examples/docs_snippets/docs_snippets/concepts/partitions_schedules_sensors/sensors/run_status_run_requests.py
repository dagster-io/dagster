from dagster import (
    DagsterRunStatus,
    RunRequest,
    SkipReason,
    run_failure_sensor,
    run_status_sensor,
)

status_reporting_job = None

# start
@run_status_sensor(
    pipeline_run_status=DagsterRunStatus.SUCCESS,
    response_job=status_reporting_job,
)
def report_status_sensor(context):
    # this condition prevents the sensor from triggering status_reporting_job again after it succeeds
    if context.dagster_run.pipeline_name != status_reporting_job.name:
        run_config = {
            "ops": {
                "status_report": {
                    "config": {"job_name": context.dagster_run.pipeline_name}
                }
            }
        }
        return RunRequest(run_key=None, run_config=run_config)
    else:
        return SkipReason("Don't report status of status_reporting_job")


# end

# start_job_failure


@run_failure_sensor(response_job=status_reporting_job)
def report_failure_sensor(context):
    run_config = {
        "ops": {
            "status_report": {"config": {"job_name": context.dagster_run.pipeline_name}}
        }
    }
    return RunRequest(run_key=None, run_config=run_config)


# end_job_failure
