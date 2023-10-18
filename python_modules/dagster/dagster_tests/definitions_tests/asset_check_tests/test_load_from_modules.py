from dagster import AssetKey, load_assets_from_modules
from dagster._core.definitions.load_asset_checks_from_modules import load_asset_checks_from_modules

from dagster_tests.definitions_tests.decorators_tests.test_asset_check_decorator import (
    execute_assets_and_checks,
)

from . import checks_module
from .checks_module import asset_check_1


def test_load_asset_checks_from_modules():
    checks = load_asset_checks_from_modules([checks_module])
    assert len(checks) == 1

    assert checks[0].spec.asset_key == asset_check_1.asset_key
    assert checks[0].spec.name == asset_check_1.name

    result = execute_assets_and_checks(
        asset_checks=checks, assets=load_assets_from_modules([checks_module])
    )
    assert result.success

    assert len(result.get_asset_check_evaluations()) == 1
    assert result.get_asset_check_evaluations()[0].passed
    assert result.get_asset_check_evaluations()[0].asset_key == asset_check_1.asset_key
    assert result.get_asset_check_evaluations()[0].check_name == "asset_check_1"


def test_load_asset_checks_from_modules_prefix():
    checks = load_asset_checks_from_modules([checks_module], asset_key_prefix="foo")
    assert len(checks) == 1

    assert checks[0].spec.asset_key == AssetKey(["foo", "asset_1"])
    assert checks[0].spec.name == asset_check_1.name

    result = execute_assets_and_checks(
        asset_checks=checks, assets=load_assets_from_modules([checks_module], key_prefix="foo")
    )
    assert result.success

    assert len(result.get_asset_check_evaluations()) == 1
    assert result.get_asset_check_evaluations()[0].passed
    assert result.get_asset_check_evaluations()[0].asset_key == AssetKey(["foo", "asset_1"])
    assert result.get_asset_check_evaluations()[0].check_name == "asset_check_1"
