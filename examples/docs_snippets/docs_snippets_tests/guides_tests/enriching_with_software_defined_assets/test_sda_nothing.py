from docs_snippets.guides.dagster.enriching_with_software_defined_assets.sda_nothing import (
    repo,
)


def test_sda_nothing():
    assert repo.get_job("users_recommender_job").success
