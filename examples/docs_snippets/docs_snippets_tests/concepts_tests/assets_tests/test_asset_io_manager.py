from docs_snippets.concepts.assets.asset_io_manager import defs


def test():
    assets_defs = defs.get_repository_def().asset_graph.assets_defs
    assert len(assets_defs) == 2
