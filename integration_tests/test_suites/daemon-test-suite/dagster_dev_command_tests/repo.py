from dagster import DefaultSensorStatus, RunRequest, repository, sensor
from dagster._legacy import pipeline, solid


@solid()
def foo_solid(_):
    pass


@pipeline
def foo_pipeline():
    foo_solid()


@pipeline
def other_foo_pipeline():
    foo_solid()


@sensor(job_name="foo_pipeline", default_status=DefaultSensorStatus.RUNNING)
def always_on_sensor(_context):
    return RunRequest(run_key="only_one", run_config={}, tags={})


@repository
def example_repo():
    return [foo_pipeline, always_on_sensor]


@repository
def other_example_repo():
    return [other_foo_pipeline]
