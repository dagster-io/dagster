import importlib
import textwrap
from pathlib import Path

import dagster as dg
from dagster.components.core.tree import LegacyAutoloadingComponentTree

LOCATION_PATH = Path(__file__).parent.parent / "code_locations" / "python_script_location"


def test_load_from_path() -> None:
    module = importlib.import_module(
        "dagster_tests.components_tests.code_locations.python_script_location.defs"
    )
    tree = LegacyAutoloadingComponentTree.from_module(
        defs_module=module, project_root=Path(__file__).parent
    )
    assert (
        tree.to_string_representation(include_load_and_build_status=True)
        == textwrap.dedent(
            """
            ├── multiple_component_instances
            │   ├── component.py[bar]
            │   └── component.py[foo]
            ├── multiple_component_instances_defs_py
            │   ├── component.py[bar]
            │   └── component.py[foo]
            ├── multiple_definitions_calls
            │   └── defs.py
            ├── script_python_decl
            │   └── component.py
            ├── scripts
            │   ├── defs.yaml[0] (PythonScriptComponent)
            │   ├── defs.yaml[1] (PythonScriptComponent)
            │   └── defs.yaml[2] (PythonScriptComponent)
            └── triple_dash_scripts
                ├── defs.yaml[0] (PythonScriptComponent)
                ├── defs.yaml[1] (PythonScriptComponent)
                └── defs.yaml[2] (PythonScriptComponent)
            """
        ).strip()
    )
    tree.load_root_component()
    assert (
        tree.to_string_representation(include_load_and_build_status=True)
        == textwrap.dedent(
            """
            ├── multiple_component_instances (loaded)
            │   ├── component.py[bar] (loaded)
            │   └── component.py[foo] (loaded)
            ├── multiple_component_instances_defs_py (loaded)
            │   ├── component.py[bar] (loaded)
            │   └── component.py[foo] (loaded)
            ├── multiple_definitions_calls (loaded)
            │   └── defs.py (loaded)
            ├── script_python_decl (loaded)
            │   └── component.py (loaded)
            ├── scripts (loaded)
            │   ├── defs.yaml[0] (PythonScriptComponent) (loaded)
            │   ├── defs.yaml[1] (PythonScriptComponent) (loaded)
            │   └── defs.yaml[2] (PythonScriptComponent) (loaded)
            └── triple_dash_scripts (loaded)
                ├── defs.yaml[0] (PythonScriptComponent) (loaded)
                ├── defs.yaml[1] (PythonScriptComponent) (loaded)
                └── defs.yaml[2] (PythonScriptComponent) (loaded)
            """
        ).strip()
    )

    defs = tree.build_defs()
    assert defs.resolve_asset_graph().get_all_asset_keys() == {
        dg.AssetKey("a"),
        dg.AssetKey("b"),
        dg.AssetKey("c"),
        dg.AssetKey("up1"),
        dg.AssetKey("up2"),
        dg.AssetKey("override_key"),
        dg.AssetKey("cool_script"),
        dg.AssetKey("a_dash"),
        dg.AssetKey("b_dash"),
        dg.AssetKey("c_dash"),
        dg.AssetKey("up1_dash"),
        dg.AssetKey("up2_dash"),
        dg.AssetKey("override_key_dash"),
        dg.AssetKey("foo"),
        dg.AssetKey("bar"),
        dg.AssetKey("foo_def_py"),
        dg.AssetKey("bar_def_py"),
        dg.AssetKey("from_defs_one"),
        dg.AssetKey("from_defs_two"),
    }
    assert defs.component_tree

    assert (
        tree.to_string_representation(include_load_and_build_status=True)
        == textwrap.dedent(
            """
            ├── multiple_component_instances (built)
            │   ├── component.py[bar] (built)
            │   └── component.py[foo] (built)
            ├── multiple_component_instances_defs_py (built)
            │   ├── component.py[bar] (built)
            │   └── component.py[foo] (built)
            ├── multiple_definitions_calls (built)
            │   └── defs.py (built)
            ├── script_python_decl (built)
            │   └── component.py (built)
            ├── scripts (built)
            │   ├── defs.yaml[0] (PythonScriptComponent) (built)
            │   ├── defs.yaml[1] (PythonScriptComponent) (built)
            │   └── defs.yaml[2] (PythonScriptComponent) (built)
            └── triple_dash_scripts (built)
                ├── defs.yaml[0] (PythonScriptComponent) (built)
                ├── defs.yaml[1] (PythonScriptComponent) (built)
                └── defs.yaml[2] (PythonScriptComponent) (built)
            """
        ).strip()
    )


def test_load_from_location_path() -> None:
    module = importlib.import_module(
        "dagster_tests.components_tests.code_locations.python_script_location.defs.scripts"
    )
    defs = dg.load_defs(module, project_root=Path(__file__).parent)

    assert defs.resolve_asset_graph().get_all_asset_keys() == {
        dg.AssetKey("a"),
        dg.AssetKey("b"),
        dg.AssetKey("c"),
        dg.AssetKey("up1"),
        dg.AssetKey("up2"),
        dg.AssetKey("override_key"),
    }
