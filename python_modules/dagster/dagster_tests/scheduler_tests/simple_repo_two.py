from dagster import job, op, repository, schedule


@op
def the_op():
    pass


@job
def the_job():
    the_op()


# changed simple schedule from running (2 0 * * *) to running (1 0 * * *)
@schedule(cron_schedule="0 1 * * *", job_name="the_job", execution_timezone="UTC")
def simple_schedule():
    return {}


@repository
def the_repo():
    return [
        the_job,
        simple_schedule,
    ]
