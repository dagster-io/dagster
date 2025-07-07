import dagster as dg
from dagster import DagsterRunStatus

success_job_defs_name = (
    "dagster_tests.daemon_sensor_tests.locations_for_xlocation_sensor_test.job_defs"
)


@dg.op
def an_op():
    pass


@dg.job
def target_job():
    an_op()


@dg.run_status_sensor(
    run_status=DagsterRunStatus.SUCCESS,
    monitored_jobs=[dg.CodeLocationSelector(success_job_defs_name)],
    request_job=target_job,
)
def success_sensor(_):
    return dg.RunRequest(job_name="target_job")


@dg.run_status_sensor(
    run_status=DagsterRunStatus.SUCCESS,
    monitored_jobs=[
        dg.JobSelector(location_name=success_job_defs_name, job_name="another_success_job")
    ],
    request_job=target_job,
)
def success_of_another_job_sensor(_):
    return dg.RunRequest(job_name="target_job")


@dg.run_status_sensor(
    monitor_all_repositories=True,
    run_status=DagsterRunStatus.SUCCESS,
    request_job=target_job,
)
def all_code_locations_run_status_sensor():
    return dg.RunRequest(job_name="target_job")


@dg.run_failure_sensor(
    monitor_all_code_locations=True,
    request_job=target_job,
)
def all_code_locations_run_failure_sensor():
    return dg.RunRequest(job_name="target_job")


defs = dg.Definitions(
    sensors=[
        success_sensor,
        success_of_another_job_sensor,
        all_code_locations_run_failure_sensor,
        all_code_locations_run_status_sensor,
    ],
    jobs=[target_job],
)
