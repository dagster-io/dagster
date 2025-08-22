import importlib
import textwrap
from pathlib import Path
from typing import Union

import dagster as dg
import pytest
from dagster._utils.env import environ
from dagster.components.core.component_tree import (
    ComponentTree,
    ComponentTreeException,
    LegacyAutoloadingComponentTree,
)
from dagster.components.core.decl import ComponentDecl, DefsFolderDecl, PythonFileDecl, YamlFileDecl
from dagster.components.core.defs_module import ComponentPath, CompositeYamlComponent
from dagster_shared import check

from dagster_tests.components_tests.integration_tests.component_loader import (
    chdir as chdir,
    sync_load_test_component_defs,
)
from dagster_tests.components_tests.utils import create_project_from_components


def assert_tree_node_structure_matches(
    tree: ComponentTree, structure: dict[Union[str, ComponentPath], type[ComponentDecl]]
):
    nodes_by_path = dict(tree.find_root_decl().iterate_path_component_decl_pairs())
    unrepresented_paths = set(nodes_by_path.keys())

    for path, expected_type in structure.items():
        component_path = (
            path
            if isinstance(path, ComponentPath)
            else ComponentPath.from_path(path=tree.defs_module_path / Path(path), instance_key=None)
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
            "__init__.py": PythonFileDecl,
            "explicit_file_relative_imports": DefsFolderDecl,
            "explicit_file_relative_imports/some_file.py": PythonFileDecl,
            "explicit_file_relative_imports/some_other_file.py": PythonFileDecl,
        },
    )
    defs = component_tree.build_defs()
    assert {spec.key for spec in defs.resolve_all_asset_specs()} == {
        dg.AssetKey("asset_in_some_file"),
        dg.AssetKey("asset_in_some_other_file"),
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
            "__init__.py": PythonFileDecl,
            "explicit_file_relative_imports_init": DefsFolderDecl,
            "explicit_file_relative_imports_init/__init__.py": PythonFileDecl,
            "explicit_file_relative_imports_init/some_other_file.py": PythonFileDecl,
        },
    )
    defs = component_tree.build_defs()
    assert {spec.key for spec in defs.resolve_all_asset_specs()} == {
        dg.AssetKey("asset_in_init_file"),
        dg.AssetKey("asset_in_some_other_file"),
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
            "__init__.py": PythonFileDecl,
            "explicit_file_relative_imports_complex/definitions.py": PythonFileDecl,  # no folder bc definitions.py special name
            # rest not loaded because of definitions.py
            # "explicit_file_relative_imports_complex/some_other_file.py": CompositePythonDecl,
            # "explicit_file_relative_imports_complex/submodule": DefsFolderDecl,
            # "explicit_file_relative_imports_complex/submodule/__init__.py": CompositePythonDecl,
        },
    )
    defs = component_tree.build_defs()
    assert {spec.key for spec in defs.resolve_all_asset_specs()} == {
        dg.AssetKey("asset_in_some_file"),
        dg.AssetKey("asset_in_submodule"),
    }


def test_definitions_component_validation_error() -> None:
    with pytest.raises(ComponentTreeException) as e:
        sync_load_test_component_defs("definitions/validation_error_file")

    assert "└── definitions.py" in str(e.value)

    underlying_validation_error = e.value.__cause__

    assert "defs.yaml:4" in str(underlying_validation_error)


def test_definitions_component_with_multiple_definitions_objects() -> None:
    with pytest.raises(ComponentTreeException) as e:
        sync_load_test_component_defs("definitions/definitions_object_multiple")

    assert "my_defs.py (error)" in str(e.value)

    underlying_validation_error = e.value.__cause__

    assert "Found multiple Definitions objects in" in str(underlying_validation_error)


@pytest.mark.parametrize("component_tree", ["definitions/single_file"], indirect=True)
def test_autoload_single_file(component_tree: ComponentTree) -> None:
    assert not component_tree.is_fully_loaded()
    component_tree.load_root_component()
    assert component_tree.is_fully_loaded()
    defs = component_tree.build_defs()
    assert component_tree.has_built_all_defs()

    assert component_tree.state_tracker.get_direct_load_dependents(
        ComponentPath.from_resolvable(component_tree.defs_module_path, "single_file/some_file.py"),
    ) == {ComponentPath.from_resolvable(component_tree.defs_module_path, "single_file")}

    assert component_tree.state_tracker.get_direct_defs_dependents(
        ComponentPath.from_resolvable(component_tree.defs_module_path, "single_file/some_file.py"),
    ) == {ComponentPath.from_resolvable(component_tree.defs_module_path, "single_file")}

    assert component_tree.state_tracker.get_direct_load_dependents(
        ComponentPath.from_resolvable(component_tree.defs_module_path, "single_file")
    ) == {ComponentPath.from_resolvable(component_tree.defs_module_path, ".")}

    assert component_tree.state_tracker.get_direct_load_dependents(
        ComponentPath.from_resolvable(component_tree.defs_module_path, "__init__.py")
    ) == {ComponentPath.from_resolvable(component_tree.defs_module_path, ".")}

    assert {spec.key for spec in defs.resolve_all_asset_specs()} == {dg.AssetKey("an_asset")}
    assert (
        component_tree.to_string_representation()
        == textwrap.dedent(
            """
        ├── __init__.py
        └── single_file
            └── some_file.py
        """
        ).strip()
    )


@pytest.mark.parametrize("component_tree", ["definitions/multiple_files"], indirect=True)
def test_autoload_multiple_files(component_tree: ComponentTree) -> None:
    defs = component_tree.build_defs()
    assert {spec.key for spec in defs.resolve_all_asset_specs()} == {
        dg.AssetKey("asset_in_some_file"),
        dg.AssetKey("asset_in_other_file"),
    }
    assert (
        component_tree.to_string_representation()
        == textwrap.dedent(
            """
        ├── __init__.py
        └── multiple_files
            ├── other_file.py
            └── some_file.py
        """
        ).strip()
    )


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
        dg.AssetKey("asset_in_some_file"),
        dg.AssetKey("asset_in_other_file"),
    }


@pytest.mark.parametrize("component_tree", ["definitions/definitions_at_levels"], indirect=True)
def test_autoload_definitions_nested(component_tree: ComponentTree) -> None:
    assert isinstance(component_tree.find_root_decl(), DefsFolderDecl)
    assert_tree_node_structure_matches(
        component_tree,
        {
            ".": DefsFolderDecl,
            "__init__.py": PythonFileDecl,
            "definitions_at_levels": DefsFolderDecl,
            "definitions_at_levels/top_level.py": PythonFileDecl,
            "definitions_at_levels/defs_object/definitions.py": PythonFileDecl,  # no folder bc definitions.py special name
            "definitions_at_levels/loose_defs": DefsFolderDecl,
            "definitions_at_levels/loose_defs/asset.py": PythonFileDecl,
            "definitions_at_levels/loose_defs/inner": DefsFolderDecl,
            "definitions_at_levels/loose_defs/inner/asset.py": PythonFileDecl,
            "definitions_at_levels/loose_defs/inner/innerer": DefsFolderDecl,
            "definitions_at_levels/loose_defs/inner/innerer/asset.py": PythonFileDecl,
            "definitions_at_levels/loose_defs/inner/innerer/innerest/definitions.py": PythonFileDecl,  # no folder bc definitions.py special name
            "definitions_at_levels/loose_defs/inner/innerer/in_init": DefsFolderDecl,
            "definitions_at_levels/loose_defs/inner/innerer/in_init/__init__.py": PythonFileDecl,
        },
    )
    defs = component_tree.build_defs()
    assert {spec.key for spec in defs.resolve_all_asset_specs()} == {
        dg.AssetKey("top_level"),
        dg.AssetKey("defs_obj_inner"),
        dg.AssetKey("defs_obj_outer"),
        dg.AssetKey("innerest_defs"),
        dg.AssetKey("innerer"),
        dg.AssetKey("inner"),
        dg.AssetKey("in_loose_defs"),
        dg.AssetKey("in_init"),
    }


def test_autoload_definitions_nested_with_config() -> None:
    ENV_VAL = "abc_xyz"
    tags_by_spec = {
        dg.AssetKey("top_level"): {
            "top_level_tag": "true",
        },
        dg.AssetKey("defs_obj_inner"): {
            "top_level_tag": "true",
            "defs_object_tag": "true",
        },
        dg.AssetKey("defs_obj_outer"): {
            "top_level_tag": "true",
            "defs_object_tag": "true",
        },
        dg.AssetKey("inner"): {
            "top_level_tag": "true",
            "loose_defs_tag": "true",
        },
        dg.AssetKey("innerer"): {
            "top_level_tag": "true",
            "loose_defs_tag": "true",
        },
        dg.AssetKey("in_loose_defs"): {
            "top_level_tag": "true",
            "loose_defs_tag": "true",
        },
        dg.AssetKey("innerest_defs"): {
            "top_level_tag": "true",
            "loose_defs_tag": "true",
            "env_tag": ENV_VAL,
            "another_level_tag": "true",
        },
        dg.AssetKey("in_init"): {
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
                ComponentPath.from_path(tree.defs_module_path, 0): DefsFolderDecl,
                "top_level.py": PythonFileDecl,
                "loose_defs": YamlFileDecl,
                ComponentPath.from_path(tree.defs_module_path / "loose_defs", 0): DefsFolderDecl,
                "loose_defs/asset.py": PythonFileDecl,
                "loose_defs/inner": DefsFolderDecl,
                "loose_defs/inner/asset.py": PythonFileDecl,
                "loose_defs/inner/innerer": DefsFolderDecl,
                "loose_defs/inner/innerer/asset.py": PythonFileDecl,
                "loose_defs/inner/innerer/another_level": YamlFileDecl,
                ComponentPath.from_path(
                    tree.defs_module_path / "loose_defs/inner/innerer/another_level", 0
                ): DefsFolderDecl,
                "loose_defs/inner/innerer/another_level/in_init": DefsFolderDecl,
                "loose_defs/inner/innerer/another_level/in_init/__init__.py": PythonFileDecl,
                "loose_defs/inner/innerer/another_level/innerest/definitions.py": PythonFileDecl,  # no folder bc definitions.py special name
                "defs_object": YamlFileDecl,
                ComponentPath.from_path(tree.defs_module_path / "defs_object", 0): DefsFolderDecl,
                "defs_object/defs_object/definitions.py": PythonFileDecl,  # no folder bc definitions.py special name
            },
        )

        defs_root_yaml = check.inst(tree.load_root_component(), CompositeYamlComponent)
        defs_root = check.inst(defs_root_yaml.components[0], dg.DefsFolderComponent)
        for comp in defs_root.iterate_components():
            if isinstance(comp, dg.DefsFolderComponent):
                assert comp.children
            if isinstance(comp, CompositeYamlComponent):
                for child in comp.components:
                    if isinstance(child, dg.DefsFolderComponent):
                        assert child.children


@pytest.mark.parametrize("component_tree", ["definitions/backcompat_components"], indirect=True)
def test_autoload_backcompat_components(component_tree: ComponentTree) -> None:
    defs = component_tree.build_defs()
    assert {spec.key for spec in defs.resolve_all_asset_specs()} == {dg.AssetKey("foo")}


@pytest.mark.parametrize(
    "terminate_autoloading_on_keyword_files, expected_keys",
    [
        (
            True,
            {
                dg.AssetKey("asset_in_definitions_py"),
                dg.AssetKey("asset_in_component_py"),
                dg.AssetKey("top_level"),
                # This is technically a breaking change, but it feels uncommon enough to me
                dg.AssetKey("asset_only_in_asset_py_with_component_py"),
            },
        ),
        (
            False,
            {
                dg.AssetKey("asset_in_definitions_py"),
                dg.AssetKey("top_level"),
                dg.AssetKey("asset_in_inner"),
                dg.AssetKey("asset_only_in_asset_py_with_component_py"),
                dg.AssetKey("defs_obj_outer"),
                dg.AssetKey("not_included"),
                dg.AssetKey("asset_in_component_py"),
            },
        ),
    ],
)
def test_autoload_definitions_new_flag(
    terminate_autoloading_on_keyword_files: bool, expected_keys: set[dg.AssetKey]
) -> None:
    if not terminate_autoloading_on_keyword_files:
        defs = dg.load_from_defs_folder(
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
        defs = dg.load_defs(
            module,
            project_root=Path(__file__).parent,
        )

    assert {spec.key for spec in defs.resolve_all_asset_specs()} == expected_keys


def test_combined_python_defs_and_components() -> None:
    defs = dg.load_from_defs_folder(
        project_root=Path(__file__).parent
        / "integration_test_defs"
        / "definitions"
        / "both_python_defs_and_components",
    )

    assert {spec.key for spec in defs.resolve_all_asset_specs()} == {
        dg.AssetKey("asset_in_component_py"),
        dg.AssetKey("top_level"),
    }
