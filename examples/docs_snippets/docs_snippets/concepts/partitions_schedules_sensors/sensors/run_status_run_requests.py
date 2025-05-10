import dagster as dg

status_reporting_job = None


# start
@dg.run_status_sensor(
    run_status=dg.DagsterRunStatus.SUCCESS,
    request_job=status_reporting_job,
)
def report_status_sensor(context: dg.RunStatusSensorContext):
    # this condition prevents the sensor from triggering status_reporting_job again after it succeeds
    if context.dagster_run.job_name != status_reporting_job.name:
        run_config = {
            "ops": {
                "status_report": {"config": {"job_name": context.dagster_run.job_name}}
            }
        }
        return dg.RunRequest(run_key=None, run_config=run_config)
    else:
        return dg.SkipReason("Don't report status of status_reporting_job")


# end

# start_job_failure


@dg.run_failure_sensor(request_job=status_reporting_job)
def report_failure_sensor(context: dg.RunFailureSensorContext):
    run_config = {
        "ops": {"status_report": {"config": {"job_name": context.dagster_run.job_name}}}
    }
    return dg.RunRequest(run_key=None, run_config=run_config)


# end_job_failure
