from dagster import RunRequest, ScheduleDefinition, asset, job, op, repository, sensor


@asset
def asset1():
    pass


@asset
def asset2():
    pass


@asset(group_name="mygroup")
def asset3():
    pass


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
        asset1,
        asset2,
        asset3,
        job1_schedule,
        job2_sensor,
        job3,
    ]
