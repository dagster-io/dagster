import dagster as dg


@dg.op
def the_op():
    pass


@dg.job
def the_job():
    the_op()


@dg.schedule(cron_schedule="0 2 * * *", job_name="the_job", execution_timezone="UTC")
def simple_schedule():
    return {}


@dg.repository
def the_repo():
    return [
        the_job,
        simple_schedule,
    ]
