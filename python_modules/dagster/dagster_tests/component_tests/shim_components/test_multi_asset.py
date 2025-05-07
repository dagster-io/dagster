from dagster import AssetsDefinition
from dagster.components.lib.shim_components.multi_asset import MultiAssetScaffolder
from dagster_tests.component_tests.shim_components.shim_test_utils import (
    execute_ruff_compliance_test,
    execute_scaffolder_and_get_symbol,
)


def test_multi_asset_scaffolder():
    """Test that the MultiAssetScaffolder creates valid Python code that evaluates to a multi-asset."""
    scaffolder = MultiAssetScaffolder()
    multi_asset_fn = execute_scaffolder_and_get_symbol(scaffolder, "my_multi_asset")

    # Verify that the function creates a valid multi-asset
    assert isinstance(multi_asset_fn, AssetsDefinition)


def test_multi_asset_scaffolder_ruff_compliance():
    """Test that the generated code passes ruff linting."""
    scaffolder = MultiAssetScaffolder()
    code = scaffolder.get_text("my_multi_asset", None)
    execute_ruff_compliance_test(code)
