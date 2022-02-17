from docs_snippets.concepts.assets.asset_io_manager_prod_local import (
    local_asset_group,
    prod_asset_group,
)


def test_asset_groups():
    assert len(local_asset_group.assets) == 2
    assert len(prod_asset_group.assets) == 2
