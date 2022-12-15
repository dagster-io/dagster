from docs_snippets.concepts.assets.cross_code_location_asset import defs


def test_repository_asset_groups():
    assert defs.get_job_def("__ASSET_JOB").execute_in_process().success
    assert defs.get_job_def("__ASSET_JOB").execute_in_process().success
