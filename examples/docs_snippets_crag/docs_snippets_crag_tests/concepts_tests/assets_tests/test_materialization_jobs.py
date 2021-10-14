from docs_snippets_crag.concepts.assets.materialization_jobs import my_user_model_job


def test_pipelines_compile_and_execute():
    jobs = [my_user_model_job]
    for job in jobs:
        result = job.execute_in_process()
        assert result.success
