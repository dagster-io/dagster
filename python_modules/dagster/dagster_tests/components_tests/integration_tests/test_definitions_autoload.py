import pytest
from dagster import AssetKey, Definitions
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._utils.env import environ
from dagster.components.component.component import ComponentRequirements
from pydantic import ValidationError

from dagster_tests.components_tests.integration_tests.component_loader import (
    chdir as chdir,
    sync_load_test_component_defs,
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

    assert "component.yaml:4" in str(e.value)


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
@pytest.mark.parametrize(
    "requirements", ["definitions/definitions_object_relative_imports"], indirect=True
)
def test_autoload_definitions_object(
    defs: Definitions, requirements: ComponentRequirements
) -> None:
    assert {spec.key for spec in defs.get_all_asset_specs()} == {
        AssetKey("asset_in_some_file"),
        AssetKey("asset_in_other_file"),
    }
    assert set(requirements.env.keys()) == {"DEFS_OBJECT_ENV"}


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


@pytest.mark.parametrize(
    "requirements", ["definitions/definitions_at_levels_with_config"], indirect=True
)
def test_autoload_definitions_nested_requirements(requirements: ComponentRequirements) -> None:
    # 3 env vars explicitly declared at each level, one implicit (from UDF)
    assert set(requirements.env.keys()) == {
        "TOP_LEVEL_ENV",
        "DEFS_OBJECT_ENV",
        "LOOSE_DEFS_ENV",
        "MY_ENV_VAR",
    }


@pytest.mark.parametrize("requirements", ["definitions/many_env_vars_sample"], indirect=True)
def test_requirements_with_many_env_vars(requirements: ComponentRequirements) -> None:
    assert set(requirements.env.keys()) == {
        "MY_ENV_VAR",
        "MY_INT_ENV_VAR",
        "MY_UNLISTED_ENV_VAR",
    }
