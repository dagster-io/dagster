from docs_snippets.concepts.assets.multi_assets import (
    my_assets,
    my_complex_assets,
    my_function,
    split_actions,
)


def test_basic():
    assert len(my_function.asset_keys) == 2


def test_io_manager():
    assert len(my_assets.asset_keys) == 2


def test_subset():
    assert len(split_actions.asset_keys) == 2


def test_inter_asset_deps():
    assert len(my_complex_assets.asset_keys) == 2
