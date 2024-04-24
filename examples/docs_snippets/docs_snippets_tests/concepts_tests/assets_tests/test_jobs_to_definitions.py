from docs_snippets.concepts.assets.jobs_to_definitions import defs


def test_build_job_doc_snippet():
    assert defs.get_job_def("number_asset_job").execute_in_process().success
