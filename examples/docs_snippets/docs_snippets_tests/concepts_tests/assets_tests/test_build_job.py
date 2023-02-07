from docs_snippets.concepts.assets.build_job import defs


def test_build_job_doc_snippet():
    assert defs.get_job_def("all_assets_job").execute_in_process().success
    assert defs.get_job_def("asset1_job").execute_in_process().success
