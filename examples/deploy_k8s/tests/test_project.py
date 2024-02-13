from ..example_project.example_repo.repo import example_job


def test_example_project():
    assert example_job.execute_in_process().success
