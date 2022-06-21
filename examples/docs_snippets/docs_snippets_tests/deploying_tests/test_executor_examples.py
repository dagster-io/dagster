from docs_snippets.deploying.executors.executors import other_job, the_job, the_repo


def test_executor_direct_examples():
    assert the_job.execute_in_process().success
    assert other_job.execute_in_process().success


def test_executor_repo_examples():
    assert the_repo.get_job("the_job").execute_in_process().success
    assert the_repo.get_job("op_job").execute_in_process().success
