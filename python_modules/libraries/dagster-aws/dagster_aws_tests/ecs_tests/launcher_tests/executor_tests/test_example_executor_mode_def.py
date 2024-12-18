# ruff: isort: skip_file
# fmt: off
# start_marker
from dagster_aws.ecs import ecs_executor

from dagster import job, op


@op(
    tags={"ecs/cpu": "256", "ecs/memory": "512"},
)
def ecs_op():
    pass


@job(executor_def=ecs_executor)
def ecs_job():
    ecs_op()


# end_marker
# fmt: on


def test_mode():
    assert ecs_job
