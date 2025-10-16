import dagster as dg
import pytest
from dagster.components.core.component_tree import ComponentTree

from dagster_tests.components_tests.integration_tests.component_loader import chdir as chdir


@pytest.mark.parametrize("component_tree", ["pythonic_components/relative_import"], indirect=True)
def test_pythonic_components_relative_import(component_tree: ComponentTree) -> None:
    defs = component_tree.build_defs()
    assert {spec.key for spec in defs.resolve_all_asset_specs()} == {dg.AssetKey("value")}
