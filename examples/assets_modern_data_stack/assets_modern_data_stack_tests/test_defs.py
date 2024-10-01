from assets_modern_data_stack.definitions import defs


def test_defs_can_load():
    # Repo will have a single implicit job for all the assets, since they all
    # have the same partitioning scheme
    assert defs.get_implicit_global_asset_job_def()
    assert defs.get_job_def("all_assets")
