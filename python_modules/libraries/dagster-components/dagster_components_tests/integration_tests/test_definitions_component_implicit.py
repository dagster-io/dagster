import sys
from pathlib import Path

import pytest
from dagster._core.definitions.asset_key import AssetKey
from dagster._utils import pushd

from dagster_components_tests.integration_tests.component_loader import load_test_component_defs


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


def test_definitions_component_with_definitions_object() -> None:
    with pytest.raises(ValueError, match="Found a Definitions object"):
        load_test_component_defs("definitions_implicit/definitions_object_relative_imports")
