from dagster._core.definitions import job, op, repository


@op
def hello_world(_):
    pass


@job
def hello_world_job():
    hello_world()


@repository(name="hello_world_repository_name")
def named_hello_world_repository():
    return [hello_world_job]
