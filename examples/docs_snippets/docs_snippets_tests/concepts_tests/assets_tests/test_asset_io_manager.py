from docs_snippets.concepts.assets.asset_io_manager import defs


def test():
    assert (
        len(defs.get_repository_def()._assets_defs_by_key)
        == 2  # pylint: disable=protected-access
    )
