import pytest
from dagster import AssetKey, Definitions

from dagster_components_tests.integration_tests.component_loader import (
    chdir as chdir,
    sync_load_test_component_defs,
)


@pytest.mark.parametrize("defs", ["definitions_implicit/single_file"], indirect=True)
def test_definitions_component_with_single_file(defs: Definitions) -> None:
    assert {spec.key for spec in defs.get_all_asset_specs()} == {AssetKey("an_asset")}


@pytest.mark.parametrize("defs", ["definitions_implicit/multiple_files"], indirect=True)
def test_definitions_component_with_multiple_files(defs: Definitions) -> None:
    assert {spec.key for spec in defs.get_all_asset_specs()} == {
        AssetKey("asset_in_some_file"),
        AssetKey("asset_in_other_file"),
    }


@pytest.mark.parametrize("defs", ["definitions_implicit/empty"], indirect=True)
def test_definitions_component_empty(defs: Definitions) -> None:
    assert len(defs.get_all_asset_specs()) == 0


def test_definitions_component_with_definitions_object() -> None:
    with pytest.raises(ValueError, match="Found a Definitions object"):
        sync_load_test_component_defs("definitions_implicit/definitions_object_relative_imports")
