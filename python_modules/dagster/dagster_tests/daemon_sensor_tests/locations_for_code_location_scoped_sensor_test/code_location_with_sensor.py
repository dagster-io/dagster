from dagster import DagsterRunStatus, Definitions, RunRequest, job, op, run_status_sensor


@op
def an_op():
    pass


@job
def success_job():
    an_op()


@job
def target_job():
    an_op()


@run_status_sensor(
    run_status=DagsterRunStatus.SUCCESS,
    monitored_jobs=[success_job],
    request_job=target_job,
)
def success_sensor(_):
    return RunRequest(job_name="target_job")


defs = Definitions(jobs=[success_job, target_job], sensors=[success_sensor])
