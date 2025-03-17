import pytest
from dagster import AssetKey, Definitions

from dagster_components_tests.integration_tests.component_loader import chdir as chdir


@pytest.mark.parametrize("defs", ["definitions_autoload/single_file"], indirect=True)
def test_autoload_single_file(defs: Definitions) -> None:
    assert {spec.key for spec in defs.get_all_asset_specs()} == {AssetKey("an_asset")}


@pytest.mark.parametrize("defs", ["definitions_autoload/multiple_files"], indirect=True)
def test_autoload_multiple_files(defs: Definitions) -> None:
    assert {spec.key for spec in defs.get_all_asset_specs()} == {
        AssetKey("asset_in_some_file"),
        AssetKey("asset_in_other_file"),
    }


@pytest.mark.parametrize("defs", ["definitions_autoload/empty"], indirect=True)
def test_autoload_empty(defs: Definitions) -> None:
    assert len(defs.get_all_asset_specs()) == 0


@pytest.mark.parametrize(
    "defs", ["definitions_autoload/definitions_object_relative_imports"], indirect=True
)
def test_autoload_definitions_object(defs: Definitions) -> None:
    assert {spec.key for spec in defs.get_all_asset_specs()} == {
        AssetKey("asset_in_some_file"),
        AssetKey("asset_in_other_file"),
    }


@pytest.mark.parametrize("defs", ["definitions_autoload/definitions_at_levels"], indirect=True)
def test_autoload_definitions_nested(defs: Definitions) -> None:
    assert {spec.key for spec in defs.get_all_asset_specs()} == {
        AssetKey("top_level"),
        AssetKey("defs_obj_inner"),
        AssetKey("defs_obj_outer"),
        AssetKey("innerest_defs"),
        AssetKey("innerer"),
        AssetKey("inner"),
        AssetKey("in_loose_defs"),
        AssetKey("in_init"),
    }
