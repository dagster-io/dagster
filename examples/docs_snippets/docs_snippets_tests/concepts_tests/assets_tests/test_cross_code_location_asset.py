from docs_snippets.concepts.assets.cross_code_location_asset import (
    code_location_1,
    code_location_2,
)


def test_repository_asset_groups():
    assert code_location_1.get_job_def("__ASSET_JOB").execute_in_process().success
    assert code_location_2.get_job_def("__ASSET_JOB").execute_in_process().success
