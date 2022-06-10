from docs_snippets.concepts.assets.cross_repository_asset import (
    repository_a,
    repository_b,
)


def test_repository_asset_groups():
    assert repository_a.get_job("__ASSET_JOB").execute_in_process().success
    assert repository_b.get_job("__ASSET_JOB").execute_in_process().success
