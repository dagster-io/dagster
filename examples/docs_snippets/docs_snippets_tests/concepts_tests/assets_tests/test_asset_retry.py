from dagster import materialize
from docs_snippets.concepts.assets.asset_retry import retried_asset


def test_retry_examples():
    # just that it runs
    assert materialize([retried_asset])
