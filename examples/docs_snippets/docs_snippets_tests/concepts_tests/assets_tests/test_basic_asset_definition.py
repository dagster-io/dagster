from docs_snippets.concepts.assets.basic_asset_definition import my_asset


def test_basic_asset_definition():
    assert my_asset.op.name == "my_asset"
