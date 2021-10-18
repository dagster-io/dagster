from dagster import RunRequest, ScheduleDefinition, job, repository, sensor


@job
def job1():
    ...


@job
def job2():
    ...


@job
def job3():
    ...


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
