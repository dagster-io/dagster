from assets_modern_data_stack import assets_modern_data_stack


def test_repo_can_load():
    assets_modern_data_stack.load_all_definitions()

    # Repo should have only one "default" asset group, which is represented a "__ASSET_JOB" job
    assert [job.name for job in assets_modern_data_stack.get_all_jobs()] == ["__ASSET_JOB"]
