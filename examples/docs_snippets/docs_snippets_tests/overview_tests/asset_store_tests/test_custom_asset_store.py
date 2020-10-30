from dagster import execute_pipeline
from docs_snippets.overview.asset_stores.custom_asset_store import my_pipeline


def test_custom_asset_store():
    execute_pipeline(my_pipeline)
