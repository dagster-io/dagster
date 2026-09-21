from docs_snippets.guides.build.assets.asset_definition_metadata import small_petals


def test():
    assert small_petals.op.outs["result"].metadata
