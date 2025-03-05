import sys
from pathlib import Path

import pytest
from dagster._core.definitions.asset_key import AssetKey
from dagster._utils import pushd
from dagster_components.components.definitions_component.component import DefinitionsComponent
from dagster_components.scaffold import scaffold_component_instance
from pydantic import ValidationError

from dagster_components_tests.integration_tests.component_loader import load_test_component_defs
from dagster_components_tests.utils import temp_code_location_bar


@pytest.fixture(autouse=True)
def chdir():
    with pushd(str(Path(__file__).parent.parent)):
        sys.path.append(str(Path(__file__).parent))
        yield


def test_definitions_component_with_default_file() -> None:
    defs = load_test_component_defs("definitions/default_file")
    assert {spec.key for spec in defs.get_all_asset_specs()} == {AssetKey("an_asset")}


def test_definitions_component_with_explicit_file() -> None:
    defs = load_test_component_defs("definitions/explicit_file")
    assert {spec.key for spec in defs.get_all_asset_specs()} == {AssetKey("asset_in_some_file")}


def test_definitions_component_with_explicit_file_relative_imports() -> None:
    defs = load_test_component_defs("definitions/explicit_file_relative_imports")
    assert {spec.key for spec in defs.get_all_asset_specs()} == {
        AssetKey("asset_in_some_file"),
        AssetKey("asset_in_some_other_file"),
    }


def test_definitions_component_with_explicit_file_relative_imports_init() -> None:
    defs = load_test_component_defs("definitions/explicit_file_relative_imports_init")
    assert {spec.key for spec in defs.get_all_asset_specs()} == {
        AssetKey("asset_in_init_file"),
        AssetKey("asset_in_some_other_file"),
    }


def test_definitions_component_with_explicit_file_relative_imports_complex() -> None:
    defs = load_test_component_defs("definitions/explicit_file_relative_imports_complex")
    assert {spec.key for spec in defs.get_all_asset_specs()} == {
        AssetKey("asset_in_some_file"),
        AssetKey("asset_in_submodule"),
    }


def test_definitions_component_validation_error() -> None:
    with pytest.raises(ValidationError) as e:
        load_test_component_defs("definitions/validation_error_file")

    assert "component.yaml:4" in str(e.value)


def test_definitions_component_with_definitions_object() -> None:
    defs = load_test_component_defs("definitions/definitions_object_relative_imports")
    assert {spec.key for spec in defs.get_all_asset_specs()} == {
        AssetKey("asset_in_some_file"),
        AssetKey("asset_in_some_other_file"),
    }


def test_definitions_component_with_multiple_definitions_objects() -> None:
    with pytest.raises(ValueError, match="Found multiple Definitions objects in my_defs.py"):
        load_test_component_defs("definitions/definitions_object_multiple")


def test_scaffold_sensor() -> None:
    with temp_code_location_bar():
        instance_path = Path(".") / "some_instance"
        scaffold_component_instance(
            instance_path, DefinitionsComponent, "DefinitionsComponent", {"object_type": "sensor"}
        )
        assert {p.name for p in instance_path.iterdir()} == {"definitions.py", "component.yaml"}

        with open(instance_path / "definitions.py") as f:
            assert "@dg.sensor" in f.read()
