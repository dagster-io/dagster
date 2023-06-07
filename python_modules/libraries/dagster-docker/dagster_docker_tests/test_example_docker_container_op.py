# ruff: isort: skip_file
# fmt: off
# start_marker
from dagster_docker import docker_container_op

from dagster import job

first_op = docker_container_op.configured(
    {
        "image": "busybox",
        "command": ["echo HELLO"],
    },
    name="first_op",
)
second_op = docker_container_op.configured(
    {
        "image": "busybox",
        "command": ["echo GOODBYE"],
    },
    name="second_op",
)

@job
def full_job():
    second_op(first_op())
# end_marker
# fmt: on


def test_docker_container_op():
    assert full_job
