import importlib
import shutil
import sys
from pathlib import Path

import pytest
from dagster import AssetKey
from dagster._utils import pushd
from dagster_components.core.component import DefinitionsModuleCache

from dagster_components_tests.integration_tests.component_loader import load_test_component_defs
from dagster_components_tests.utils import create_project_from_components


@pytest.fixture(autouse=True)
def chdir():
    with pushd(str(Path(__file__).parent.parent)):
        sys.path.append(str(Path(__file__).parent))
        yield


def test_definitions_component_with_single_file() -> None:
    defs = load_test_component_defs("definitions_implicit/single_file")
    assert {spec.key for spec in defs.get_all_asset_specs()} == {AssetKey("an_asset")}


def test_definitions_component_with_multiple_files() -> None:
    defs = load_test_component_defs("definitions_implicit/multiple_files")
    assert {spec.key for spec in defs.get_all_asset_specs()} == {
        AssetKey("asset_in_some_file"),
        AssetKey("asset_in_other_file"),
    }


def test_definitions_component_empty() -> None:
    defs = load_test_component_defs("definitions_implicit/empty")
    assert len(defs.get_all_asset_specs()) == 0


def test_definitions_component_with_multiple_defs() -> None:
    with pytest.raises(ValueError, match="Found multiple files"):
        load_test_component_defs("definitions_implicit/definitions_object_invalid")


def test_definitions_component_top_level_and_nested() -> None:
    with create_project_from_components() as (project_root, project_name):
        # move the contents of the top_level path to the defs folder
        defs_dir = Path(project_root) / project_name / "defs"
        shutil.rmtree(defs_dir)
        shutil.copytree(
            Path(__file__).parent / "integration_test_defs" / "definitions_implicit" / "defs",
            defs_dir,
        )

        module = importlib.import_module(f"{project_name}.defs")
        assert not (Path(project_root) / project_name / "defs" / "top_level").exists()

        defs = DefinitionsModuleCache(resources={}).load_defs(module=module)
        assert {spec.key for spec in defs.get_all_asset_specs()} == {
            AssetKey("top_level_1"),
            AssetKey("top_level_2"),
            AssetKey("nested_1"),
            AssetKey("nested_2"),
            AssetKey("nested_3"),
            AssetKey("nested_4"),
            AssetKey("nested_5"),
        }


def test_definitions_component_with_mulitple_definitions_objects() -> None:
    defs = load_test_component_defs("definitions_implicit/definitions_object_multiple")
    assert {spec.key for spec in defs.get_all_asset_specs()} == {AssetKey("a1"), AssetKey("a2")}
