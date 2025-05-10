from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey
from dagster._core.definitions.decorators.asset_check_decorator import asset_check
from dagster.components.component_scaffolding import parse_params_model
from dagster.components.lib.shim_components.asset_check import (
    AssetCheckScaffolder,
    AssetCheckScaffoldParams,
)
from dagster_tests.component_tests.shim_components.shim_test_utils import (
    execute_ruff_compliance_test,
    execute_scaffolder_and_get_symbol,
)


def test_asset_check_scaffolder():
    """Test that the AssetCheckScaffolder creates valid Python code that evaluates to an asset check."""
    scaffolder = AssetCheckScaffolder()
    # Since the scaffolder returns a commented-out template, we should just verify it's a string
    code = scaffolder.get_text("my_check", AssetCheckScaffoldParams(asset_key="my_asset"))
    assert isinstance(code, str)
    assert "asset_check" in code
    assert "AssetCheckExecutionContext" in code
    assert "AssetCheckResult" in code


def test_asset_check_scaffolder_with_asset_key():
    """Test that the AssetCheckScaffolder creates valid code when given an asset key."""
    scaffolder = AssetCheckScaffolder()
    params = AssetCheckScaffoldParams(asset_key="my_asset")
    checks_def = execute_scaffolder_and_get_symbol(scaffolder, "my_check", params)

    # Verify that the function creates a valid asset check
    assert isinstance(checks_def, AssetChecksDefinition)
    assert len(checks_def.check_keys) == 1
    check_key = next(iter(checks_def.check_keys))
    assert check_key == AssetCheckKey(AssetKey("my_asset"), "my_check")


def test_asset_check_scaffolder_ruff_compliance():
    """Test that the generated code passes ruff linting."""
    scaffolder = AssetCheckScaffolder()
    code = scaffolder.get_text("my_check", AssetCheckScaffoldParams(asset_key="my_asset"))
    execute_ruff_compliance_test(code)


def test_asset_check_scaffolder_params_flow():
    """Test that params flow correctly through the scaffolding process."""
    # Parse params through the CLI function
    json_params = '{"asset_key": "my_asset"}'

    params_model = parse_params_model(asset_check, json_params)

    # Use the parsed params to generate code and get the symbol
    scaffolder = AssetCheckScaffolder()
    checks_def = execute_scaffolder_and_get_symbol(scaffolder, "my_check", params_model)

    # Verify we got a valid asset check definition
    assert isinstance(checks_def, AssetChecksDefinition)
    assert len(checks_def.check_keys) == 1
    check_key = next(iter(checks_def.check_keys))
    assert check_key == AssetCheckKey(AssetKey("my_asset"), "my_check")
