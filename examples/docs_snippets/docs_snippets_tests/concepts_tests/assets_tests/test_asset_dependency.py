from docs_snippets.concepts.assets.asset_dependency import (
    upstream_asset,
    downstream_asset,
)


def test_asset_dependency():
    assert upstream_asset.op.name == "upstream_asset"
    assert downstream_asset.op.name == "downstream_asset"
