from dagster import job, op, repository, schedule


@op
def the_op():
    pass


@job
def the_job():
    the_op()


@schedule(cron_schedule="0 2 * * *", job_name="the_job", execution_timezone="UTC")
def simple_schedule():
    return {}


@repository
def the_repo():
    return [
        the_job,
        simple_schedule,
    ]
