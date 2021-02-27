from dagster import RunRequest, pipeline, repository, schedule, sensor, solid


@solid()
def foo_solid(_):
    pass


@pipeline
def foo_pipeline():
    foo_solid()


@pipeline
def other_foo_pipeline():
    foo_solid()


@schedule(
    pipeline_name="foo_pipeline",
    cron_schedule="*/1 * * * *",
)
def never_run_schedule(_context):
    return {}


@sensor(pipeline_name="foo_pipeline")
def never_on_sensor(_context):
    return RunRequest(run_key=None, run_config={}, tags={})


@repository
def example_repo():
    return [foo_pipeline, never_run_schedule, never_on_sensor]


@repository
def other_example_repo():
    return [other_foo_pipeline]
