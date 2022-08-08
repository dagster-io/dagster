from dagster import RunRequest, op, repository, schedule, sensor
from dagster._legacy import pipeline


@op()
def foo_op(_):
    pass


@pipeline
def foo_pipeline():
    foo_op()


@pipeline
def other_foo_pipeline():
    foo_op()


@schedule(
    job_name="foo_pipeline",
    cron_schedule="*/1 * * * *",
)
def always_run_schedule():
    return {}


@sensor(job_name="foo_pipeline")
def always_on_sensor(_context):
    return RunRequest(run_key=None, run_config={}, tags={})


@repository
def example_repo():
    return [foo_pipeline, always_run_schedule, always_on_sensor]


@repository
def other_example_repo():
    return [other_foo_pipeline]
