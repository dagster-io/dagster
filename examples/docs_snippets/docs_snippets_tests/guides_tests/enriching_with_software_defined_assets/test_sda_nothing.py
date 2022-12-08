from docs_snippets.guides.dagster.enriching_with_software_defined_assets.sda_nothing import (
    defs,
)


def test_sda_nothing():
    assert defs.get_job("users_recommender_job").execute_in_process().success
