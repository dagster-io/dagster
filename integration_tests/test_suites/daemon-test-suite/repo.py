from dagster import job, op, RunRequest, repository, schedule, sensor


@op()
def foo_op(_):
    pass


@job
def foo_job():
    foo_op()


@job
def other_foo_job():
    foo_op()


@schedule(
    job_name="foo_job",
    cron_schedule="*/1 * * * *",
)
def always_run_schedule():
    return {}


@sensor(job_name="foo_job")
def always_on_sensor(_context):
    return RunRequest(run_key=None, run_config={}, tags={})


@repository
def example_repo():
    return [foo_job, always_run_schedule, always_on_sensor]


@repository
def other_example_repo():
    return [other_foo_job]
