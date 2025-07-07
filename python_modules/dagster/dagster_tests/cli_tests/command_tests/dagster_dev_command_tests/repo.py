import os

import dagster as dg
from bar import foo_op  # requires working_directory  # type: ignore
from dagster import DefaultSensorStatus


@dg.job
def foo_job():
    foo_op()


@dg.job
def other_foo_job():
    foo_op()


@dg.sensor(job_name="foo_job", default_status=DefaultSensorStatus.RUNNING)
def always_on_sensor(_context):
    return dg.RunRequest(run_key="only_one", run_config={}, tags={})


@dg.repository
def example_repo():
    return [foo_job, always_on_sensor]


@dg.repository
def other_example_repo():
    return [other_foo_job]


if os.getenv("CHECK_DAGSTER_DEV") and not os.getenv("DAGSTER_IS_DEV_CLI"):
    raise Exception("DAGSTER_DEV env var not set")
