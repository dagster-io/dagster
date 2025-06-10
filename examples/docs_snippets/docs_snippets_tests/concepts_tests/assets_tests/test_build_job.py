from docs_snippets.concepts.assets.build_job import all_assets_job, sugary_cereals_job


def test_build_job_doc_snippet():
    assert all_assets_job.execute_in_process().success
    assert sugary_cereals_job.execute_in_process().success
