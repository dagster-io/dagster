import importlib
from pathlib import Path
from typing import Union

import pytest
from dagster import AssetKey, load_defs, load_from_defs_folder
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._utils.env import environ
from dagster.components.core.decl import (
    ComponentDecl,
    DagsterDefsDecl,
    DefsFolderDecl,
    YamlFileDecl,
)
from dagster.components.core.defs_module import (
    ComponentPath,
    CompositeYamlComponent,
    DefsFolderComponent,
)
from dagster.components.core.tree import ComponentTree, LegacyAutoloadingComponentTree
from dagster_shared import check
from pydantic import ValidationError

from dagster_tests.components_tests.integration_tests.component_loader import (
    chdir as chdir,
    sync_load_test_component_defs,
)
from dagster_tests.components_tests.utils import create_project_from_components


def assert_tree_node_structure_matches(
    tree: ComponentTree, structure: dict[Union[str, ComponentPath], type[ComponentDecl]]
):
    nodes_by_path = {
        ComponentPath(
            file_path=node_path.file_path.relative_to(tree.defs_module_path),
            instance_key=node_path.instance_key,
        ): node
        for node_path, node in tree.find_root_decl().iterate_path_component_decl_pairs()
    }
    unrepresented_paths = set(nodes_by_path.keys())

    for path, expected_type in structure.items():
        component_path = (
            path
            if isinstance(path, ComponentPath)
            else ComponentPath(file_path=Path(path), instance_key=None)
        )
        matching_node = next(
            (
                decl
                for node, decl in nodes_by_path.items()
                if node.file_path.as_posix() == component_path.file_path.as_posix()
                and node.instance_key == component_path.instance_key
            ),
            None,
        )
        assert matching_node is not None, (
            f"Could not find {component_path} in paths {list(nodes_by_path.keys())}"
        )
        assert isinstance(matching_node, expected_type), (
            f"Expected {expected_type} at {component_path} but got {type(matching_node)}"
        )
        unrepresented_paths.remove(component_path)
    output_str = "\n".join(
        f"{path.file_path}{f'@{path.instance_key}' if path.instance_key is not None else ''}: {type(nodes_by_path[path])}"
        for path in unrepresented_paths
    )
    assert not unrepresented_paths, f"Unrepresented paths: {output_str}"


@pytest.mark.parametrize(
    "component_tree", ["definitions/explicit_file_relative_imports"], indirect=True
)
def test_definitions_component_with_explicit_file_relative_imports(
    component_tree: ComponentTree,
) -> None:
    assert isinstance(component_tree.find_root_decl(), DefsFolderDecl)
    assert_tree_node_structure_matches(
        component_tree,
        {
            ".": DefsFolderDecl,
            "__init__.py": DagsterDefsDecl,
            "explicit_file_relative_imports": DefsFolderDecl,
            "explicit_file_relative_imports/some_file.py": DagsterDefsDecl,
            "explicit_file_relative_imports/some_other_file.py": DagsterDefsDecl,
        },
    )
    defs = component_tree.build_defs()
    assert {spec.key for spec in defs.resolve_all_asset_specs()} == {
        AssetKey("asset_in_some_file"),
        AssetKey("asset_in_some_other_file"),
    }


@pytest.mark.parametrize(
    "component_tree", ["definitions/explicit_file_relative_imports_init"], indirect=True
)
def test_definitions_component_with_explicit_file_relative_imports_init(
    component_tree: ComponentTree,
) -> None:
    assert isinstance(component_tree.find_root_decl(), DefsFolderDecl)
    assert_tree_node_structure_matches(
        component_tree,
        {
            ".": DefsFolderDecl,
            "__init__.py": DagsterDefsDecl,
            "explicit_file_relative_imports_init": DefsFolderDecl,
            "explicit_file_relative_imports_init/__init__.py": DagsterDefsDecl,
            "explicit_file_relative_imports_init/some_other_file.py": DagsterDefsDecl,
        },
    )
    defs = component_tree.build_defs()
    assert {spec.key for spec in defs.resolve_all_asset_specs()} == {
        AssetKey("asset_in_init_file"),
        AssetKey("asset_in_some_other_file"),
    }


@pytest.mark.parametrize(
    "component_tree", ["definitions/explicit_file_relative_imports_complex"], indirect=True
)
def test_definitions_component_with_explicit_file_relative_imports_complex(
    component_tree: ComponentTree,
) -> None:
    assert isinstance(component_tree.find_root_decl(), DefsFolderDecl)
    assert_tree_node_structure_matches(
        component_tree,
        {
            ".": DefsFolderDecl,
            "__init__.py": DagsterDefsDecl,
            "explicit_file_relative_imports_complex/definitions.py": DagsterDefsDecl,  # no folder bc definitions.py special name
            # rest not loaded because of definitions.py
            # "explicit_file_relative_imports_complex/some_other_file.py": DagsterDefsDecl,
            # "explicit_file_relative_imports_complex/submodule": DefsFolderDecl,
            # "explicit_file_relative_imports_complex/submodule/__init__.py": DagsterDefsDecl,
        },
    )
    defs = component_tree.build_defs()
    assert {spec.key for spec in defs.resolve_all_asset_specs()} == {
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


@pytest.mark.parametrize("component_tree", ["definitions/single_file"], indirect=True)
def test_autoload_single_file(component_tree: ComponentTree) -> None:
    defs = component_tree.build_defs()
    assert {spec.key for spec in defs.resolve_all_asset_specs()} == {AssetKey("an_asset")}


@pytest.mark.parametrize("component_tree", ["definitions/multiple_files"], indirect=True)
def test_autoload_multiple_files(component_tree: ComponentTree) -> None:
    defs = component_tree.build_defs()
    assert {spec.key for spec in defs.resolve_all_asset_specs()} == {
        AssetKey("asset_in_some_file"),
        AssetKey("asset_in_other_file"),
    }


@pytest.mark.parametrize("component_tree", ["definitions/empty"], indirect=True)
def test_autoload_empty(component_tree: ComponentTree) -> None:
    defs = component_tree.build_defs()
    assert len(defs.resolve_all_asset_specs()) == 0


@pytest.mark.parametrize(
    "component_tree", ["definitions/definitions_object_relative_imports"], indirect=True
)
def test_autoload_definitions_object(component_tree: ComponentTree) -> None:
    defs = component_tree.build_defs()
    assert {spec.key for spec in defs.resolve_all_asset_specs()} == {
        AssetKey("asset_in_some_file"),
        AssetKey("asset_in_other_file"),
    }


@pytest.mark.parametrize("component_tree", ["definitions/definitions_at_levels"], indirect=True)
def test_autoload_definitions_nested(component_tree: ComponentTree) -> None:
    assert isinstance(component_tree.find_root_decl(), DefsFolderDecl)
    assert_tree_node_structure_matches(
        component_tree,
        {
            ".": DefsFolderDecl,
            "__init__.py": DagsterDefsDecl,
            "definitions_at_levels": DefsFolderDecl,
            "definitions_at_levels/top_level.py": DagsterDefsDecl,
            "definitions_at_levels/defs_object/definitions.py": DagsterDefsDecl,  # no folder bc definitions.py special name
            "definitions_at_levels/loose_defs": DefsFolderDecl,
            "definitions_at_levels/loose_defs/asset.py": DagsterDefsDecl,
            "definitions_at_levels/loose_defs/inner": DefsFolderDecl,
            "definitions_at_levels/loose_defs/inner/asset.py": DagsterDefsDecl,
            "definitions_at_levels/loose_defs/inner/innerer": DefsFolderDecl,
            "definitions_at_levels/loose_defs/inner/innerer/asset.py": DagsterDefsDecl,
            "definitions_at_levels/loose_defs/inner/innerer/innerest/definitions.py": DagsterDefsDecl,  # no folder bc definitions.py special name
            "definitions_at_levels/loose_defs/inner/innerer/in_init": DefsFolderDecl,
            "definitions_at_levels/loose_defs/inner/innerer/in_init/__init__.py": DagsterDefsDecl,
        },
    )
    defs = component_tree.build_defs()
    assert {spec.key for spec in defs.resolve_all_asset_specs()} == {
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
        specs_by_key = {spec.key: spec for spec in defs.resolve_all_asset_specs()}
        assert tags_by_spec.keys() == specs_by_key.keys()
        for key, tags in tags_by_spec.items():
            assert specs_by_key[key].tags == tags


def test_ignored_empty_dir():
    path_str = "definitions/definitions_at_levels_with_config"
    src_path = Path(path_str)
    with create_project_from_components(path_str) as (project_root, project_name):
        module = importlib.import_module(f"{project_name}.defs.{src_path.stem}")
        tree = LegacyAutoloadingComponentTree.from_module(
            defs_module=module, project_root=project_root
        )

        check.inst(tree.find_root_decl(), YamlFileDecl)
        assert_tree_node_structure_matches(
            tree,
            {
                ".": YamlFileDecl,
                ComponentPath(file_path=Path("."), instance_key=0): DefsFolderDecl,
                "top_level.py": DagsterDefsDecl,
                "loose_defs": YamlFileDecl,
                ComponentPath(file_path=Path("loose_defs"), instance_key=0): DefsFolderDecl,
                "loose_defs/asset.py": DagsterDefsDecl,
                "loose_defs/inner": DefsFolderDecl,
                "loose_defs/inner/asset.py": DagsterDefsDecl,
                "loose_defs/inner/innerer": DefsFolderDecl,
                "loose_defs/inner/innerer/asset.py": DagsterDefsDecl,
                "loose_defs/inner/innerer/another_level": YamlFileDecl,
                ComponentPath(
                    file_path=Path("loose_defs/inner/innerer/another_level"), instance_key=0
                ): DefsFolderDecl,
                "loose_defs/inner/innerer/another_level/in_init": DefsFolderDecl,
                "loose_defs/inner/innerer/another_level/in_init/__init__.py": DagsterDefsDecl,
                "loose_defs/inner/innerer/another_level/innerest/definitions.py": DagsterDefsDecl,  # no folder bc definitions.py special name
                "defs_object": YamlFileDecl,
                ComponentPath(file_path=Path("defs_object"), instance_key=0): DefsFolderDecl,
                "defs_object/defs_object/definitions.py": DagsterDefsDecl,  # no folder bc definitions.py special name
            },
        )

        defs_root_yaml = check.inst(tree.load_root_component(), CompositeYamlComponent)
        defs_root = check.inst(defs_root_yaml.components[0], DefsFolderComponent)
        for comp in defs_root.iterate_components():
            if isinstance(comp, DefsFolderComponent):
                assert comp.children
            if isinstance(comp, CompositeYamlComponent):
                for child in comp.components:
                    if isinstance(child, DefsFolderComponent):
                        assert child.children


@pytest.mark.parametrize("component_tree", ["definitions/backcompat_components"], indirect=True)
def test_autoload_backcompat_components(component_tree: ComponentTree) -> None:
    defs = component_tree.build_defs()
    assert {spec.key for spec in defs.resolve_all_asset_specs()} == {AssetKey("foo")}


@pytest.mark.parametrize(
    "terminate_autoloading_on_keyword_files, expected_keys",
    [
        (
            True,
            {
                AssetKey("asset_in_definitions_py"),
                AssetKey("asset_in_component_py"),
                AssetKey("top_level"),
            },
        ),
        (
            False,
            {
                # asset_in_component_py is not included
                AssetKey("asset_in_definitions_py"),
                AssetKey("top_level"),
                AssetKey("asset_in_inner"),
                AssetKey("asset_only_in_asset_py_with_component_py"),
                AssetKey("defs_obj_outer"),
                AssetKey("not_included"),
            },
        ),
    ],
)
def test_autoload_definitions_new_flag(
    terminate_autoloading_on_keyword_files: bool, expected_keys: set[AssetKey]
) -> None:
    if not terminate_autoloading_on_keyword_files:
        defs = load_from_defs_folder(
            project_root=Path(__file__).parent
            / "integration_test_defs"
            / "definitions"
            / "special_names_at_levels",
        )
    else:
        # Flag is not present on load_defs_folder
        module = importlib.import_module(
            "dagster_tests.components_tests.integration_tests.integration_test_defs.definitions.special_names_at_levels.special_names_at_levels"
        )
        defs = load_defs(
            module,
            project_root=Path(__file__).parent,
        )

    assert {spec.key for spec in defs.resolve_all_asset_specs()} == expected_keys
