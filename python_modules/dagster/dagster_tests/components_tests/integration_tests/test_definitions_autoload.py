import importlib
from pathlib import Path

import pytest
from dagster import AssetKey, Definitions
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._utils.env import environ
from dagster.components.core.context import ComponentLoadContext
from dagster.components.core.defs_module import CompositeYamlComponent, DefsFolderComponent
from dagster_shared import check
from pydantic import ValidationError

from dagster_tests.components_tests.integration_tests.component_loader import (
    chdir as chdir,
    sync_load_test_component_defs,
)
from dagster_tests.components_tests.utils import (
    create_project_from_components,
    get_underlying_component,
)


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

    assert "defs.yaml:4" in str(e.value)


def test_definitions_component_with_multiple_definitions_objects() -> None:
    with pytest.raises(
        DagsterInvalidDefinitionError, match="Found multiple Definitions objects in"
    ):
        sync_load_test_component_defs("definitions/definitions_object_multiple")


@pytest.mark.parametrize("defs", ["definitions/single_file"], indirect=True)
def test_autoload_single_file(defs: Definitions) -> None:
    assert {spec.key for spec in defs.get_all_asset_specs()} == {AssetKey("an_asset")}


@pytest.mark.parametrize("defs", ["definitions/multiple_files"], indirect=True)
def test_autoload_multiple_files(defs: Definitions) -> None:
    assert {spec.key for spec in defs.get_all_asset_specs()} == {
        AssetKey("asset_in_some_file"),
        AssetKey("asset_in_other_file"),
    }


@pytest.mark.parametrize("defs", ["definitions/empty"], indirect=True)
def test_autoload_empty(defs: Definitions) -> None:
    assert len(defs.get_all_asset_specs()) == 0


@pytest.mark.parametrize("defs", ["definitions/definitions_object_relative_imports"], indirect=True)
def test_autoload_definitions_object(defs: Definitions) -> None:
    assert {spec.key for spec in defs.get_all_asset_specs()} == {
        AssetKey("asset_in_some_file"),
        AssetKey("asset_in_other_file"),
    }


@pytest.mark.parametrize("defs", ["definitions/definitions_at_levels"], indirect=True)
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


def test_autoload_definitions_nested_with_config() -> None:
    ENV_VAL = "abc_xyz"
    tags_by_spec = {
        AssetKey("top_level"): {
            "top_level_tag": "true",
        },
        AssetKey("defs_obj_inner"): {
            "top_level_tag": "true",
            "defs_object_tag": "true",
        },
        AssetKey("defs_obj_outer"): {
            "top_level_tag": "true",
            "defs_object_tag": "true",
        },
        AssetKey("inner"): {
            "top_level_tag": "true",
            "loose_defs_tag": "true",
        },
        AssetKey("innerer"): {
            "top_level_tag": "true",
            "loose_defs_tag": "true",
        },
        AssetKey("in_loose_defs"): {
            "top_level_tag": "true",
            "loose_defs_tag": "true",
        },
        AssetKey("innerest_defs"): {
            "top_level_tag": "true",
            "loose_defs_tag": "true",
            "env_tag": ENV_VAL,
            "another_level_tag": "true",
        },
        AssetKey("in_init"): {
            "top_level_tag": "true",
            "loose_defs_tag": "true",
            "env_tag": ENV_VAL,
            "another_level_tag": "true",
        },
    }
    with environ({"MY_ENV_VAR": ENV_VAL}):
        defs = sync_load_test_component_defs("definitions/definitions_at_levels_with_config")
        specs_by_key = {spec.key: spec for spec in defs.get_all_asset_specs()}
        assert tags_by_spec.keys() == specs_by_key.keys()
        for key, tags in tags_by_spec.items():
            assert specs_by_key[key].tags == tags


def test_ignored_empty_dir():
    path_str = "definitions/definitions_at_levels_with_config"
    src_path = Path(path_str)
    with create_project_from_components(path_str) as (project_root, project_name):
        module = importlib.import_module(f"{project_name}.defs.{src_path.stem}")
        context = ComponentLoadContext.for_module(module, project_root)
        defs_root = check.inst(get_underlying_component(context), DefsFolderComponent)
        for comp in defs_root.iterate_components():
            if isinstance(comp, DefsFolderComponent):
                assert comp.children
            if isinstance(comp, CompositeYamlComponent):
                for child in comp.components:
                    if isinstance(child, DefsFolderComponent):
                        assert child.children


@pytest.mark.parametrize("defs", ["definitions/backcompat_components"], indirect=True)
def test_autoload_backcompat_components(defs: Definitions) -> None:
    assert {spec.key for spec in defs.get_all_asset_specs()} == {AssetKey("foo")}
