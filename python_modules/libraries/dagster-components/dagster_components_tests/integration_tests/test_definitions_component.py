import pytest
from dagster import AssetKey, Definitions
from pydantic import ValidationError

from dagster_components_tests.integration_tests.component_loader import (
    chdir as chdir,
    sync_load_test_component_defs,
)


@pytest.mark.parametrize("defs", ["definitions/default_file"], indirect=True)
def test_definitions_component_with_default_file(defs: Definitions) -> None:
    assert {spec.key for spec in defs.get_all_asset_specs()} == {AssetKey("an_asset")}


@pytest.mark.parametrize("defs", ["definitions/explicit_file"], indirect=True)
def test_definitions_component_with_explicit_file(defs: Definitions) -> None:
    assert {spec.key for spec in defs.get_all_asset_specs()} == {AssetKey("asset_in_some_file")}


@pytest.mark.parametrize("defs", ["definitions/explicit_file_relative_imports"], indirect=True)
def test_definitions_component_with_explicit_file_relative_imports(defs: Definitions) -> None:
    assert {spec.key for spec in defs.get_all_asset_specs()} == {
        AssetKey("asset_in_some_file"),
        AssetKey("asset_in_some_other_file"),
    }


@pytest.mark.parametrize("defs", ["definitions/explicit_file_relative_imports_init"], indirect=True)
def test_definitions_component_with_explicit_file_relative_imports_init(defs: Definitions) -> None:
    assert {spec.key for spec in defs.get_all_asset_specs()} == {
        AssetKey("asset_in_init_file"),
        AssetKey("asset_in_some_other_file"),
    }


@pytest.mark.parametrize(
    "defs", ["definitions/explicit_file_relative_imports_complex"], indirect=True
)
def test_definitions_component_with_explicit_file_relative_imports_complex(
    defs: Definitions,
) -> None:
    assert {spec.key for spec in defs.get_all_asset_specs()} == {
        AssetKey("asset_in_some_file"),
        AssetKey("asset_in_submodule"),
    }


def test_definitions_component_validation_error() -> None:
    with pytest.raises(ValidationError) as e:
        sync_load_test_component_defs("definitions/validation_error_file")

    assert "component.yaml:4" in str(e.value)


@pytest.mark.parametrize("defs", ["definitions/definitions_object_relative_imports"], indirect=True)
def test_definitions_component_with_definitions_object(defs: Definitions) -> None:
    # defs = load_test_component_defs("definitions/definitions_object_relative_imports")
    assert {spec.key for spec in defs.get_all_asset_specs()} == {
        AssetKey("asset_in_some_file"),
        AssetKey("asset_in_some_other_file"),
    }


def test_definitions_component_with_multiple_definitions_objects() -> None:
    with pytest.raises(ValueError, match="Found multiple Definitions objects in my_defs.py"):
        sync_load_test_component_defs("definitions/definitions_object_multiple")
