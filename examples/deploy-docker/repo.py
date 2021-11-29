from dagster import job, op, repository, schedule


@op
def hello():
    return 1


@job
def my_job():
    hello()


@schedule(cron_schedule="* * * * *", job=my_job, execution_timezone="US/Central")
def my_schedule(_context):
    return {}


@repository
def deploy_docker_repository():
    return [my_job, my_schedule]
