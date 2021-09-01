from docs_snippets_crag.guides.dagster.reexecution.unreliable_job import unreliable_job


def test_job_compiles_and_executes():
    result = unreliable_job.execute_in_process()
    assert result
