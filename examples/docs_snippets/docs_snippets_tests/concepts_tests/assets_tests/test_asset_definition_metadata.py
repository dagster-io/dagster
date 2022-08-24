from docs_snippets.concepts.assets.asset_definition_metadata import my_asset


def test():
    assert my_asset.op.outs["result"].metadata
