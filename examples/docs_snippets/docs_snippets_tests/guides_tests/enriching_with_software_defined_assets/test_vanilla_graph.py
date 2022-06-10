from docs_snippets.guides.dagster.enriching_with_software_defined_assets.vanilla_graph import (
    ingest_products_and_categories,
)


def test_ingest_products_and_categories():
    assert ingest_products_and_categories.execute_in_process().success
