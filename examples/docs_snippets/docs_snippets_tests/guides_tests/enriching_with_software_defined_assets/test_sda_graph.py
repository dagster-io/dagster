from docs_snippets.guides.dagster.enriching_with_software_defined_assets.sda_graph import (
    repo,
)


def test_sda_graph():
    assert repo.get_job("products_and_categories_job").execute_in_process().success
