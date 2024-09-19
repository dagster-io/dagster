from docs_snippets.concepts.assets.asset_different_io_managers import defs


def test():
    assets_defs = defs.get_repository_def().asset_graph.assets_defs
    assert len(assets_defs) == 2
