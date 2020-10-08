from dagster_examples.gcp_data_platform.repo import gcp_repo


def test_define_repo():
    repo = gcp_repo
    assert repo.name == "gcp_repo"
    assert repo.has_pipeline("gcp_pipeline")
