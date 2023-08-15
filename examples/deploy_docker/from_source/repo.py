import time

from dagster import FilesystemIOManager, graph, job, op, repository, schedule
from dagster_docker import docker_executor


@op
def hello():
    return 1


@op
def goodbye(foo):
    return foo * 2


@op
def hanging_op():
    while True:
        time.sleep(5)


@job
def hanging_job():
    hanging_op()


@graph
def my_graph():
    goodbye(hello())


my_job = my_graph.to_job(name="my_job")
my_step_isolated_job = my_graph.to_job(
    name="my_step_isolated_job",
    executor_def=docker_executor,
    resource_defs={"io_manager": FilesystemIOManager(base_dir="/tmp/io_manager_storage")},
)


@schedule(cron_schedule="* * * * *", job=my_job, execution_timezone="US/Central")
def my_schedule(_context):
    return {}


@repository
def deploy_docker_repository():
    return [my_job, hanging_job, my_schedule, my_step_isolated_job]
