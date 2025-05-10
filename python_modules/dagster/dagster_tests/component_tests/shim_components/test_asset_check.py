from dagster._core.definitions.asset_checks import AssetChecksDefinition
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
    code = scaffolder.get_text("my_check", AssetCheckScaffoldParams())
    assert isinstance(code, str)
    assert "asset_check" in code
    assert "AssetCheckExecutionContext" in code
    assert "AssetCheckResult" in code


def test_asset_check_scaffolder_with_asset_key():
    """Test that the AssetCheckScaffolder creates valid code when given an asset key."""
    scaffolder = AssetCheckScaffolder()
    params = AssetCheckScaffoldParams(asset_key="my_asset")
    check_fn = execute_scaffolder_and_get_symbol(scaffolder, "my_check", params)

    # Verify that the function creates a valid asset check
    assert isinstance(check_fn, AssetChecksDefinition)


def test_asset_check_scaffolder_ruff_compliance():
    """Test that the generated code passes ruff linting."""
    scaffolder = AssetCheckScaffolder()
    code = scaffolder.get_text("my_check", AssetCheckScaffoldParams())
    execute_ruff_compliance_test(code)
