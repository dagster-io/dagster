from dagster_docker import docker_executor

from dagster import fs_io_manager, graph, op, repository, schedule


@op
def hello():
    return 1


@op
def goodbye(foo):
    if foo != 1:
        raise Exception("Bad io manager")
    return foo * 2


@graph
def my_graph():
    goodbye(hello())


my_job = my_graph.to_job(name="my_job")

my_step_isolated_job = my_graph.to_job(
    name="my_step_isolated_job",
    executor_def=docker_executor,
    resource_defs={"io_manager": fs_io_manager.configured({"base_dir": "/tmp/io_manager_storage"})},
)


@schedule(cron_schedule="* * * * *", job=my_job, execution_timezone="US/Central")
def my_schedule(_context):
    return {}


@repository
def deploy_docker_repository():
    return [my_job, my_step_isolated_job, my_schedule]
