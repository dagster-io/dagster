from docs_snippets.concepts.assets.asset_different_io_managers import defs


def test():
    assets_defs_by_key = (
        defs.get_repository_def()._assets_defs_by_key  # pylint: disable=protected-access
    )
    assert len(assets_defs_by_key) == 2
