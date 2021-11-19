from docs_snippets.concepts.solids_pipelines.pipeline_execution import execute_subset, my_job


def test_execute_my_job():
    result = my_job.execute_in_process()
    assert result.success


def test_solid_selection():
    execute_subset()
