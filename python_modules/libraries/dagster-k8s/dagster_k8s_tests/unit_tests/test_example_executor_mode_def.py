# start_marker
from dagster import job
from dagster_k8s import k8s_job_executor


@job(executor_def=k8s_job_executor)
def k8s_job():
    pass


# end_marker


def test_job():
    assert k8s_job
