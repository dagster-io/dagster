import pytest
from dagster import (
    AssetKey,
    Definitions,
    asset_check,
    load_asset_checks_from_current_module,
    load_asset_checks_from_modules,
    load_asset_checks_from_package_module,
    load_asset_checks_from_package_name,
    load_assets_from_modules,
    load_assets_from_package_module,
    load_assets_from_package_name,
)

from dagster_tests.definitions_tests.decorators_tests.test_asset_check_decorator import (
    execute_assets_and_checks,
)


def test_load_asset_checks_from_modules():
    from dagster_tests.definitions_tests.asset_check_tests import checks_module
    from dagster_tests.definitions_tests.asset_check_tests.checks_module import asset_check_1

    checks = load_asset_checks_from_modules([checks_module])
    assert len(checks) == 1

    asset_check_1_key = next(iter(asset_check_1.check_keys))

    check_key = next(iter(checks[0].check_keys))
    assert check_key.asset_key == asset_check_1_key.asset_key
    assert check_key.name == asset_check_1_key.name

    result = execute_assets_and_checks(
        asset_checks=checks, assets=load_assets_from_modules([checks_module])
    )
    assert result.success

    assert len(result.get_asset_check_evaluations()) == 2
    assert result.get_asset_check_evaluations()[0].passed
    assert result.get_asset_check_evaluations()[0].asset_key == asset_check_1_key.asset_key
    assert result.get_asset_check_evaluations()[0].check_name == "in_op_check"
    assert result.get_asset_check_evaluations()[1].passed
    assert result.get_asset_check_evaluations()[1].asset_key == asset_check_1_key.asset_key
    assert result.get_asset_check_evaluations()[1].check_name == asset_check_1_key.name


def test_load_asset_checks_from_modules_prefix():
    from dagster_tests.definitions_tests.asset_check_tests import checks_module

    checks = load_asset_checks_from_modules([checks_module], asset_key_prefix="foo")
    assert len(checks) == 1

    check_key = next(iter(checks[0].check_keys))
    assert check_key.asset_key == AssetKey(["foo", "asset_1"])
    assert check_key.name == "asset_check_1"

    result = execute_assets_and_checks(
        asset_checks=checks, assets=load_assets_from_modules([checks_module], key_prefix="foo")
    )
    assert result.success

    assert len(result.get_asset_check_evaluations()) == 2
    assert result.get_asset_check_evaluations()[0].passed
    assert result.get_asset_check_evaluations()[0].asset_key == AssetKey(["foo", "asset_1"])
    assert result.get_asset_check_evaluations()[0].check_name == "in_op_check"
    assert result.get_asset_check_evaluations()[1].passed
    assert result.get_asset_check_evaluations()[1].asset_key == AssetKey(["foo", "asset_1"])
    assert result.get_asset_check_evaluations()[1].check_name == "asset_check_1"


@asset_check(asset=AssetKey("asset_1"))
def check_in_current_module():
    pass


def test_load_asset_checks_from_current_module():
    checks = load_asset_checks_from_current_module(asset_key_prefix="foo")
    assert len(checks) == 1
    check_key = next(iter(checks[0].check_keys))
    assert check_key.name == "check_in_current_module"
    assert check_key.asset_key == AssetKey(["foo", "asset_1"])


@pytest.mark.parametrize(
    "load_fns",
    [
        (load_assets_from_package_module, load_asset_checks_from_package_module),
        (
            lambda package, **kwargs: load_assets_from_package_name(package.__name__, **kwargs),
            lambda package, **kwargs: load_asset_checks_from_package_name(
                package.__name__, **kwargs
            ),
        ),
    ],
)
def test_load_asset_checks_from_package(load_fns):
    from dagster_tests.definitions_tests.asset_check_tests import checks_module

    assets_load_fn, checks_load_fn = load_fns

    checks = checks_load_fn(checks_module, asset_key_prefix="foo")
    assert len(checks) == 2
    check_key_0 = next(iter(checks[0].check_keys))
    assert check_key_0.name == "asset_check_1"
    assert check_key_0.asset_key == AssetKey(["foo", "asset_1"])
    check_key_1 = next(iter(checks[1].check_keys))
    assert check_key_1.name == "submodule_check"
    assert check_key_1.asset_key == AssetKey(["foo", "asset_1"])

    assets = assets_load_fn(checks_module, key_prefix="foo")
    assert len(assets) == 1

    Definitions(assets=assets, asset_checks=checks).get_all_job_defs()
