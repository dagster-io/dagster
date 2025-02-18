import sys
from pathlib import Path

import pytest
from dagster._core.definitions.asset_key import AssetKey
from dagster._utils import pushd
from pydantic import ValidationError

from dagster_components_tests.integration_tests.component_loader import load_test_component_defs


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
