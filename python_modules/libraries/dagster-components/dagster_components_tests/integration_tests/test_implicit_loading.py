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


def test_implicit_single_file() -> None:
    defs = load_test_component_defs("implicit/single_file")
    assert {spec.key for spec in defs.get_all_asset_specs()} == {AssetKey("an_implicit_asset")}


def test_implicit_double_file() -> None:
    defs = load_test_component_defs("implicit/double_file")
    assert {spec.key for spec in defs.get_all_asset_specs()} == {
        AssetKey("asset_one"),
        AssetKey("asset_two"),
    }


def test_defs_object() -> None:
    defs = load_test_component_defs("implicit/defs_object")
    assert {spec.key for spec in defs.get_all_asset_specs()} == {
        AssetKey("in_defs_asset"),
    }
