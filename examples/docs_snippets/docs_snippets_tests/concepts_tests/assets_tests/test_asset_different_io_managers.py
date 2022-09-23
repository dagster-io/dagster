from docs_snippets.concepts.assets.asset_different_io_managers import my_repository


def test():
    assert len(my_repository._assets_defs_by_key) == 2
