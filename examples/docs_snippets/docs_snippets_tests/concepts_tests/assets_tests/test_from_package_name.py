from docs_snippets.concepts.assets.from_package_name import asset_group


def test_from_package_name():
    assert len(asset_group.assets) == 2
