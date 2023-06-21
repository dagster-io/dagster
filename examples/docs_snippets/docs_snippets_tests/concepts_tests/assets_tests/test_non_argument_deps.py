from dagster import materialize
from docs_snippets.concepts.assets.non_argument_deps import (
    downstream_asset,
    upstream_asset,
)


def test_upstream_assets():
    materialize([upstream_asset, downstream_asset])
