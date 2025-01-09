import pytest
from dagster._core.definitions.asset_key import AssetKey
from pydantic import ValidationError

from dagster_components_tests.integration_tests.component_loader import load_test_component_defs


def test_definitions_component_with_default_file() -> None:
    defs = load_test_component_defs("definitions/default_file")
    assert {spec.key for spec in defs.get_all_asset_specs()} == {AssetKey("an_asset")}


def test_definitions_component_with_explicit_file() -> None:
    defs = load_test_component_defs("definitions/explicit_file")
    assert {spec.key for spec in defs.get_all_asset_specs()} == {AssetKey("asset_in_some_file")}


def test_definitions_component_validation_error() -> None:
    with pytest.raises(ValidationError) as e:
        load_test_component_defs("definitions/validation_error_file")

    assert "component.yaml:4" in str(e.value)
