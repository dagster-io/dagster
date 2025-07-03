import dagster as dg


@dg.op
def hello_world(_):
    pass


@dg.job
def hello_world_job():
    hello_world()
