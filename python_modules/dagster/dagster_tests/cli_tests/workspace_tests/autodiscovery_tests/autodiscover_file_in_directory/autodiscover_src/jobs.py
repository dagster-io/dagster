from dagster import job, op


@op
def hello_world(_):
    pass


@job
def hello_world_job():
    hello_world()
