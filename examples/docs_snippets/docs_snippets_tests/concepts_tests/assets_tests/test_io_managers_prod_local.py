from docs_snippets.concepts.assets.asset_io_manager_prod_local import (
    local_assets,
    prod_assets,
)


def test_asset_groups():
    assert len(local_assets) == 2
    assert len(prod_assets) == 2
