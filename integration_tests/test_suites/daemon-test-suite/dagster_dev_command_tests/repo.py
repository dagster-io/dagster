import os

from bar import foo_op  # requires working_directory
from dagster import DefaultSensorStatus, RunRequest, job, repository, sensor


@job
def foo_job():
    foo_op()


@job
def other_foo_job():
    foo_op()


@sensor(job_name="foo_job", default_status=DefaultSensorStatus.RUNNING)
def always_on_sensor(_context):
    return RunRequest(run_key="only_one", run_config={}, tags={})


@repository
def example_repo():
    return [foo_job, always_on_sensor]


@repository
def other_example_repo():
    return [other_foo_job]


if os.getenv("CHECK_DAGSTER_DEV") and not os.getenv("DAGSTER_IS_DEV_CLI"):
    raise Exception("DAGSTER_DEV env var not set")
