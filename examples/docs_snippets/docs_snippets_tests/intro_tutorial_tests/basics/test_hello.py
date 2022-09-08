from docs_snippets.intro_tutorial.basics.single_op_job.hello import file_sizes_job


def test_tutorial_intro_tutorial_hello_world():
    result = file_sizes_job.execute_in_process()
    assert result.success
