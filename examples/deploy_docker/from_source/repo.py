import time

from dagster import pipeline, repository, schedule, solid


@solid
def hello():
    return 1


@solid
def hanging_solid():
    while True:
        time.sleep(5)


@pipeline
def hanging_pipeline():
    hanging_solid()


@pipeline
def my_pipeline():
    hello()


@schedule(cron_schedule="* * * * *", pipeline_name="my_pipeline", execution_timezone="US/Central")
def my_schedule(_context):
    return {}


@repository
def deploy_docker_repository():
    return [my_pipeline, hanging_pipeline, my_schedule]
