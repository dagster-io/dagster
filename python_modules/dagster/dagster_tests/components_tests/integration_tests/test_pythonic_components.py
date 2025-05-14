import pytest
from dagster import AssetKey, Definitions

from dagster_tests.components_tests.integration_tests.component_loader import chdir as chdir


@pytest.mark.parametrize("defs", ["pythonic_components/relative_import"], indirect=True)
def test_pythonic_components_relative_import(defs: Definitions) -> None:
    assert {spec.key for spec in defs.get_all_asset_specs()} == {AssetKey("value")}
