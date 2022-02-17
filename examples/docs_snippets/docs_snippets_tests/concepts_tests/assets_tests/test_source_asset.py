from docs_snippets.concepts.assets.source_asset import asset_group


def test_source_asset():
    assert len(asset_group.assets) == 1
    assert len(asset_group.source_assets) == 1
