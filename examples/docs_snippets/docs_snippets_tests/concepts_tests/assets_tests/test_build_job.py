from docs_snippets.concepts.assets.build_job import repo


def test():
    assert repo.get_job("all_assets_job").execute_in_process().success
    assert repo.get_job("asset1_job").execute_in_process().success
