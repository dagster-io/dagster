from docs_snippets.concepts.assets.asset_different_io_managers import asset_group


def test_asset_group():
    assert len(asset_group.assets) == 2
