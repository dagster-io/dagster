"""Tests for ComponentTree caching behavior, especially the mark_component_changed method."""

from pathlib import Path

import yaml
from dagster.components.core.defs_module import ComponentPath
from dagster.components.lib.executable_component.python_script_component import (
    PythonScriptComponent,
)
from dagster.components.testing import create_defs_folder_sandbox


def test_component_tree_caching_behavior():
    """Test that ComponentTree caches components and defs, and demonstrates caching behavior."""
    with create_defs_folder_sandbox(project_name="cache_test_project") as sandbox:
        # Create a base component
        base_component_path = sandbox.scaffold_component(
            defs_path="base_component",
            component_cls=PythonScriptComponent,
            defs_yaml_contents={
                "type": "dagster.PythonScriptComponent",
                "attributes": {
                    "execution": {"path": "script.py"},
                    "assets": [{"key": "base_asset"}],
                },
            },
        )
        (base_component_path / "script.py").write_text("# Empty script")

        # Create a dependent component that depends on the base component
        dependent_component_path = sandbox.scaffold_component(
            defs_path="dependent_component",
            component_cls=PythonScriptComponent,
            defs_yaml_contents={
                "type": "dagster.PythonScriptComponent",
                "attributes": {
                    "execution": {"path": "script.py"},
                    "assets": [
                        {
                            "key": "dependent_asset",
                            "deps": "{{ build_defs_at_path('base_component').resolve_all_asset_keys() }}",
                        }
                    ],
                },
            },
        )
        (dependent_component_path / "script.py").write_text("# Empty script")

        # Create an independent component with no dependency relationship
        independent_component_path = sandbox.scaffold_component(
            defs_path="independent_component",
            component_cls=PythonScriptComponent,
            defs_yaml_contents={
                "type": "dagster.PythonScriptComponent",
                "attributes": {
                    "execution": {"path": "script.py"},
                    "assets": [{"key": "independent_asset"}],
                },
            },
        )
        (independent_component_path / "script.py").write_text("# Empty script")

        with sandbox.build_component_tree() as tree:
            base_path = ComponentPath(file_path=Path("base_component"), instance_key=0)
            dependent_path = ComponentPath(file_path=Path("dependent_component"), instance_key=0)
            independent_path = ComponentPath(
                file_path=Path("independent_component"), instance_key=0
            )

            # Load all components and build defs to populate the entire tree cache
            base_component_initial = tree.load_component_at_path(base_path)
            base_defs_initial = tree.build_defs_at_path(base_path)
            independent_component_initial = tree.load_component_at_path(independent_path)
            independent_defs_initial = tree.build_defs_at_path(independent_path)
            tree.build_defs()
            assert base_defs_initial.get_assets_def("base_asset") is not None
            assert independent_defs_initial.get_assets_def("independent_asset") is not None

            # Update base component YAML
            (base_component_path / "defs.yaml").write_text(
                yaml.dump(
                    {
                        "type": "dagster.PythonScriptComponent",
                        "attributes": {
                            "execution": {"path": "script.py"},
                            "assets": [{"key": "base_asset_2"}],
                        },
                    }
                )
            )

            # Load components & build defs again - should return the same cached objects
            base_component_cached = tree.load_component_at_path(base_path)
            base_defs_cached = tree.build_defs_at_path(base_path)
            assert base_component_cached is base_component_initial
            assert base_defs_cached is base_defs_initial

            dependent_defs_initial = tree.build_defs_at_path(dependent_path)

            # Now mark the base component as changed
            tree.mark_component_changed(base_path)

            # Load the base component again - should get new instances (newly loaded)
            new_base_component = tree.load_component_at_path(base_path)
            new_base_defs = tree.build_defs_at_path(base_path)

            assert new_base_component is not base_component_cached
            assert new_base_defs is not base_defs_cached
            assert new_base_defs.get_assets_def("base_asset_2") is not None

            # Assert that the dependent component is also invalidated
            new_dependent_defs = tree.build_defs_at_path(dependent_path)
            assert new_dependent_defs is not dependent_defs_initial
            assert new_dependent_defs.get_assets_def("dependent_asset") is not None

            # Assert that the independent component is NOT invalidated (should remain cached)
            independent_component_cached = tree.load_component_at_path(independent_path)
            independent_defs_cached = tree.build_defs_at_path(independent_path)
            assert independent_component_cached is independent_component_initial
            assert independent_defs_cached is independent_defs_initial
            assert independent_defs_cached.get_assets_def("independent_asset") is not None


def test_mark_component_changed_with_nonexistent_component():
    """Test that mark_component_changed handles nonexistent components gracefully."""
    with create_defs_folder_sandbox(project_name="nonexistent_test") as sandbox:
        with sandbox.build_component_tree() as tree:
            nonexistent_path = ComponentPath(
                file_path=Path("nonexistent_component"), instance_key=None
            )

            # This should not raise an exception
            tree.mark_component_changed("nonexistent_component")

            # Verify no crashes when trying to access
            assert not tree._has_loaded_component_at_path(nonexistent_path)  # noqa: SLF001
            assert not tree._has_built_defs_at_path(nonexistent_path)  # noqa: SLF001


def test_mark_component_changed_complex_dependency_tree():
    """Test mark_component_changed with a complex dependency tree (A -> B -> C)."""
    with create_defs_folder_sandbox(project_name="complex_deps_test") as sandbox:
        # Create component A
        comp_a_path = sandbox.scaffold_component(
            defs_path="component_a",
            component_cls=PythonScriptComponent,
            defs_yaml_contents={
                "type": "dagster.PythonScriptComponent",
                "attributes": {
                    "execution": {"path": "script.py"},
                    "assets": [{"key": "asset_a"}],
                },
            },
        )
        (comp_a_path / "script.py").write_text("# Empty script")

        # Create component B (depends on A)
        comp_b_path = sandbox.scaffold_component(
            defs_path="component_b",
            component_cls=PythonScriptComponent,
            defs_yaml_contents={
                "type": "dagster.PythonScriptComponent",
                "attributes": {
                    "execution": {"path": "script.py"},
                    "assets": [{"key": "asset_b", "deps": ["asset_a"]}],
                },
            },
        )
        (comp_b_path / "script.py").write_text("# Empty script")

        # Create component C (depends on B)
        comp_c_path = sandbox.scaffold_component(
            defs_path="component_c",
            component_cls=PythonScriptComponent,
            defs_yaml_contents={
                "type": "dagster.PythonScriptComponent",
                "attributes": {
                    "execution": {"path": "script.py"},
                    "assets": [{"key": "asset_c", "deps": ["asset_b"]}],
                },
            },
        )
        (comp_c_path / "script.py").write_text("# Empty script")

        with sandbox.build_component_tree() as tree:
            # Create component paths once
            comp_a_path = ComponentPath(file_path=Path("component_a"), instance_key=None)
            comp_b_path = ComponentPath(file_path=Path("component_b"), instance_key=None)
            comp_c_path = ComponentPath(file_path=Path("component_c"), instance_key=None)

            # Load all components to populate cache
            tree.load_component_at_path("component_a")
            tree.load_component_at_path("component_b")
            tree.load_component_at_path("component_c")
            tree.build_defs_at_path("component_a")
            tree.build_defs_at_path("component_b")
            tree.build_defs_at_path("component_c")

            # Set up dependency chain: C -> B -> A
            tree.mark_component_load_dependency(comp_b_path, comp_a_path)
            tree.mark_component_load_dependency(comp_c_path, comp_b_path)

            # Verify all are cached
            assert tree._has_loaded_component_at_path(comp_a_path)  # noqa: SLF001
            assert tree._has_loaded_component_at_path(comp_b_path)  # noqa: SLF001
            assert tree._has_loaded_component_at_path(comp_c_path)  # noqa: SLF001

            # Mark component A as changed - should invalidate all dependents (B and C)
            tree.mark_component_changed("component_a")

            # Verify that A and all its transitive dependents are invalidated
            assert not tree._has_loaded_component_at_path(comp_a_path)  # noqa: SLF001
            assert not tree._has_loaded_component_at_path(comp_b_path)  # noqa: SLF001
            assert not tree._has_loaded_component_at_path(comp_c_path)  # noqa: SLF001
            assert not tree._has_built_defs_at_path(comp_a_path)  # noqa: SLF001
            assert not tree._has_built_defs_at_path(comp_b_path)  # noqa: SLF001
            assert not tree._has_built_defs_at_path(comp_c_path)  # noqa: SLF001
