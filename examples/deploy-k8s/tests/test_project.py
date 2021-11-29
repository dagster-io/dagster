from ..example_project.example_repo.repo import single_pod_job


def test_example_project():
    assert single_pod_job.execute_in_process().success
