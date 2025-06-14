from docs_snippets.concepts.assets.jobs_to_definitions import number_asset_job


def test_build_job_doc_snippet():
    assert number_asset_job.execute_in_process().success
