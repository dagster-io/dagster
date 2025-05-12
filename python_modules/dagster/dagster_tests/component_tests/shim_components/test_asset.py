from dagster._core.definitions.assets import AssetsDefinition
from dagster.components.lib.shim_components.asset import AssetScaffolder
from dagster_tests.component_tests.shim_components.shim_test_utils import (
    execute_ruff_compliance_test,
    execute_scaffolder_and_get_symbol,
)


def test_asset_scaffolder():
    """Test that the AssetScaffolder creates valid Python code that evaluates to an asset."""
    scaffolder = AssetScaffolder()
    asset_fn = execute_scaffolder_and_get_symbol(scaffolder, "my_asset")

    # Verify that the function creates a valid asset
    assert isinstance(asset_fn, AssetsDefinition)
    assert asset_fn.key.path[0] == "my_asset"


def test_asset_scaffolder_ruff_compliance():
    """Test that the generated code passes ruff linting."""
    scaffolder = AssetScaffolder()
    code = scaffolder.get_text("my_asset", None)
    execute_ruff_compliance_test(code)
