from dagster import AssetGroup
from docs_snippets.concepts.assets.non_argument_deps import upstream_asset, downstream_asset


def test_non_argument_deps():
	AssetGroup([upstream_asset, downstream_asset]).materialize()
