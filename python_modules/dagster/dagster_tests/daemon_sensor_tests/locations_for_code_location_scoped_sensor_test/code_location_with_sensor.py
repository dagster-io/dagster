import dagster as dg
from dagster import DagsterRunStatus


@dg.op
def an_op():
    pass


@dg.job
def success_job():
    an_op()


@dg.job
def target_job():
    an_op()


@dg.run_status_sensor(
    run_status=DagsterRunStatus.SUCCESS,
    monitored_jobs=[success_job],
    request_job=target_job,
)
def success_sensor(_):
    return dg.RunRequest(job_name="target_job")


defs = dg.Definitions(jobs=[success_job, target_job], sensors=[success_sensor])
