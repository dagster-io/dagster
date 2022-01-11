from dagster import RunRequest, ScheduleDefinition, job, op, repository, sensor


@op
def hello():
    pass


@job
def job1():
    hello()


@job
def job2():
    hello()


@job
def job3():
    hello()


job1_schedule = ScheduleDefinition(job=job1, cron_schedule="0 0 * * *")


@sensor(job=job2)
def job2_sensor():
    should_run = True
    if should_run:
        yield RunRequest(run_key=None, run_config={})


@repository
def my_repository():
    return [
        job1_schedule,
        job2_sensor,
        job3,
    ]
