from dagster import DagsterRunStatus, RunRequest, run_failure_sensor, run_status_sensor

status_reporting_job = None

# start
@run_status_sensor(
    pipeline_run_status=DagsterRunStatus.SUCCESS,
    run_request_job=status_reporting_job,
    ignore_job_selection=[status_reporting_job],
)
def report_status_sensor(context):
    run_config = {
        "ops": {
            "status_report": {"config": {"job_name": context.dagster_run.pipeline_name}}
        }
    }
    return RunRequest(run_key=None, run_config=run_config)


@run_failure_sensor(run_request_jobs=status_reporting_job)
def report_failure_sensor(context):
    run_config = {
        "ops": {
            "status_report": {"config": {"job_name": context.dagster_run.pipeline_name}}
        }
    }
    return RunRequest(run_key=None, run_config=run_config)


# end
