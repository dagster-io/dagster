from dagster_examples.gcp_data_platform.repo import define_repo


def test_define_repo():
    repo = define_repo()
    assert repo.name == 'gcp_pipeline'
    assert repo.has_pipeline('gcp_pipeline')
