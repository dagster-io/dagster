# ruff: isort: skip_file
# fmt: off
# start_marker
from dagster_docker import docker_executor

from dagster import job

@job(executor_def=docker_executor)
def docker_job():
    pass
# end_marker
# fmt: on


def test_mode():
    assert docker_job
