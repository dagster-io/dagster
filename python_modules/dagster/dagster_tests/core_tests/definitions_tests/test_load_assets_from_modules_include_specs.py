# test_load_assets_with_specs_duplicate.py

import types
import pytest
import dagster as dg
from dagster import AssetSpec, DagsterInvalidDefinitionError


def _make_modules_with_asset_and_spec():
    """
    Create two dynamic modules:
    - file1: contains an AssetSpec and an Asset with the same AssetKey
    - file2: imports the Asset from file1 and defines another Asset depending on it
    """
    file1 = types.ModuleType("file1")
    file2 = types.ModuleType("file2")

    # Explicit AssetSpec
    asset1_spec = AssetSpec(key="asset1")
    file1.asset1_spec = asset1_spec

    # Regular Asset
    @dg.asset
    def asset1():
        return 1

    file1.asset1 = asset1

    # Additional Asset importing asset1 from another module
    @dg.asset
    def asset2(asset1):
        return asset1 + 1

    file2.asset1 = asset1
    file2.asset2 = asset2

    return file1, file2


# -----------------------
# Tests
# -----------------------

def test_load_assets_without_specs_succeeds():
    """
    With include_specs=False:
    AssetSpec is not loaded, so there is no collision and loading succeeds.
    """
    file1, file2 = _make_modules_with_asset_and_spec()

    assets = dg.load_assets_from_modules(
        modules=[file1, file2],
        include_specs=False,
    )

    # Expect asset1 + asset2
    assert len(assets) == 2


def test_asset_plus_assetspec_does_not_raise():
    """
    With include_specs=True:
    Asset + AssetSpec with the same AssetKey should not raise an error.
    """
    file1, file2 = _make_modules_with_asset_and_spec()

    # Should not raise
    dg.load_assets_from_modules(
        modules=[file1, file2],
        include_specs=True,
    )


def test_duplicate_assets_raise():
    """
    Two different Assets with the same AssetKey should raise DagsterInvalidDefinitionError.
    """
    mod = types.ModuleType("mod")

    @dg.asset
    def asset1():
        return 1

    @dg.asset(key="asset1")
    def asset1_duplicate():
        return 2

    mod.asset1 = asset1
    mod.asset1_duplicate = asset1_duplicate

    with pytest.raises(DagsterInvalidDefinitionError):
        dg.load_assets_from_modules([mod], include_specs=False)
