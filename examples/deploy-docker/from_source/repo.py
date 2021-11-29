import time

from dagster import job, op, repository, schedule


@op
def hello():
    return 1


@op
def hanging_solid():
    while True:
        time.sleep(5)


@job
def hanging_job():
    hanging_solid()


@job
def my_job():
    hello()


@schedule(cron_schedule="* * * * *", job=my_job, execution_timezone="US/Central")
def my_schedule(_context):
    return {}


@repository
def deploy_docker_repository():
    return [my_job, hanging_job, my_schedule]
