from dagster import materialize
from docs_snippets.guides.build.assets.asset_retry import retried_asset


def test_retry_examples():
    # just that it runs
    assert materialize([retried_asset])
