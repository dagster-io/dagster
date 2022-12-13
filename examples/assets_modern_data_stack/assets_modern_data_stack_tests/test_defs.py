from assets_modern_data_stack import defs


def test_defs_can_load():
    # Repo should have only one "default" asset group, which is represented a "__ASSET_JOB" job
    assert defs.get_job_def("__ASSET_JOB")
    assert defs.get_job_def("all_assets")
