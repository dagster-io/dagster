from dagster import AssetKey
from dagster._core.definitions.load_asset_checks_from_modules import load_asset_checks_from_modules

from . import checks_module
from .checks_module import asset_check_1


def test_load_asset_checks_from_modules():
    checks = load_asset_checks_from_modules([checks_module])
    assert len(checks) == 1

    assert checks[0].spec.asset_key == asset_check_1.asset_key
    assert checks[0].spec.name == asset_check_1.name


def test_load_asset_checks_from_modules_prefix():
    checks = load_asset_checks_from_modules([checks_module], key_prefix="foo")
    assert len(checks) == 1

    assert checks[0].spec.asset_key == AssetKey(["foo", "asset_1"])
    assert checks[0].spec.name == asset_check_1.name
