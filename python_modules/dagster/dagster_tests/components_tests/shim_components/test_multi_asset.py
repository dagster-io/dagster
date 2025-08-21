import dagster as dg
from dagster.components.lib.shim_components.multi_asset import (
    MultiAssetScaffolder,
    MultiAssetScaffoldParams,
)

from dagster_tests.components_tests.shim_components.shim_test_utils import (
    execute_ruff_compliance_test,
    execute_scaffolder_and_get_symbol,
    make_test_scaffold_request,
)


def test_multi_asset_scaffolder():
    """Test that the MultiAssetScaffolder creates valid Python code that evaluates to a multi-asset."""
    scaffolder = MultiAssetScaffolder()
    params = MultiAssetScaffoldParams()
    multi_asset_fn = execute_scaffolder_and_get_symbol(scaffolder, "my_multi_asset", params)

    # Verify that the function creates a valid multi-asset
    assert isinstance(multi_asset_fn, dg.AssetsDefinition)


def test_multi_asset_scaffolder_ruff_compliance():
    """Test that the generated code passes ruff linting."""
    scaffolder = MultiAssetScaffolder()
    params = MultiAssetScaffoldParams()
    request = make_test_scaffold_request("my_multi_asset", params)
    code = scaffolder.get_text(request)
    execute_ruff_compliance_test(code)
