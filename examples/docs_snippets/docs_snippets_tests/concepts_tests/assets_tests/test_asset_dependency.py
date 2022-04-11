from docs_snippets.concepts.assets.asset_dependency import (
    downstream_asset,
    upstream_asset,
)


def test_asset_dependency():
    assert upstream_asset.op.name == "upstream_asset"
    assert downstream_asset.op.name == "downstream_asset"
