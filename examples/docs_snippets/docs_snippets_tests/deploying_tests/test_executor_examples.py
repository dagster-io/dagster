from docs_snippets.deploying.executors.executors import defs, other_job, the_job


def test_executor_direct_examples():
    assert the_job.execute_in_process().success
    assert other_job.execute_in_process().success


def test_executor_repo_examples():
    assert defs.get_job_def("the_job").execute_in_process().success
    assert defs.get_job_def("op_job").execute_in_process().success
