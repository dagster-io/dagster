import dagster as dg


@dg.op
def hello_world(_):
    pass


@dg.job
def hello_world_job():
    hello_world()


@dg.repository(name="hello_world_repository_name")
def named_hello_world_repository():
    return [hello_world_job]
