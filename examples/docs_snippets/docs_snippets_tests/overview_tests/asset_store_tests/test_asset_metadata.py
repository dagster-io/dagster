from dagster import execute_pipeline
from docs_snippets.overview.asset_stores.asset_metadata import my_pipeline


def test_asset_metadata():
    execute_pipeline(my_pipeline)
