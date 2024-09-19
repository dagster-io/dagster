# ruff: isort: skip_file
# fmt: off
# start_marker
from dagster_k8s import k8s_job_executor

from dagster import job

@job(executor_def=k8s_job_executor)
def k8s_job():
    pass
# end_marker
# fmt: on


def test_mode():
    assert k8s_job
