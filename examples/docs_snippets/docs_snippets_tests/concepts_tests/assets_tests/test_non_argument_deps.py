from docs_snippets.concepts.assets.non_argument_deps import (
    downstream_asset,
    upstream_asset,
)
from dagster._legacy import AssetGroup


def test_non_argument_deps():
    AssetGroup([upstream_asset, downstream_asset]).materialize()
