from docs_snippets.guides.build.assets.asset_materialization_metadata import table1


def test():
    assert table1().metadata  # ty: ignore[unresolved-attribute]
