"""Tests for loading sibling .py files alongside a YAML component's defs.yaml."""

import textwrap

import dagster as dg
import pytest
from dagster.components.core.component_tree import ComponentTreeException
from dagster.components.testing.utils import create_defs_folder_sandbox


class SimpleComponent(dg.Component, dg.Model, dg.Resolvable):
    """A minimal resolvable component that produces one asset."""

    asset_name: str

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        name = self.asset_name

        @dg.asset(name=name)
        def _asset(): ...

        return dg.Definitions(assets=[_asset])


_COMPONENT_TYPE = (
    "dagster_tests.components_tests.unit_tests.test_sibling_py_file_loading.SimpleComponent"
)


def test_sibling_py_file_is_loaded_alongside_yaml_component():
    """assets.py placed next to defs.yaml in a component directory should be auto-loaded."""
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            SimpleComponent,
            defs_yaml_contents={
                "type": _COMPONENT_TYPE,
                "attributes": {"asset_name": "component_asset"},
            },
        )

        # Write a sibling assets.py with an additional asset
        (defs_path / "assets.py").write_text(
            textwrap.dedent("""\
                import dagster as dg

                @dg.asset
                def sibling_asset(): ...
            """)
        )

        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (_component, defs):
            asset_keys = {spec.key for spec in defs.get_all_asset_specs()}
            assert dg.AssetKey("component_asset") in asset_keys
            assert dg.AssetKey("sibling_asset") in asset_keys


def test_sibling_py_file_with_no_dagster_defs_is_harmless():
    """A sibling .py file with no Dagster definitions is a no-op."""
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            SimpleComponent,
            defs_yaml_contents={
                "type": _COMPONENT_TYPE,
                "attributes": {"asset_name": "component_asset"},
            },
        )

        # Write a helper Python file with no Dagster definitions
        (defs_path / "utils.py").write_text(
            textwrap.dedent("""\
                def my_helper():
                    return 42
            """)
        )

        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (_component, defs):
            asset_keys = {spec.key for spec in defs.get_all_asset_specs()}
            assert dg.AssetKey("component_asset") in asset_keys
            # No extra assets from the helper file
            assert len(asset_keys) == 1


def test_sibling_py_file_asset_key_conflict_raises():
    """A sibling .py file that defines an asset with the same key as the component raises an error."""
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            SimpleComponent,
            defs_yaml_contents={
                "type": _COMPONENT_TYPE,
                "attributes": {"asset_name": "shared_asset"},
            },
        )

        # Write a sibling file that defines an asset with the same key
        (defs_path / "assets.py").write_text(
            textwrap.dedent("""\
                import dagster as dg

                @dg.asset
                def shared_asset(): ...
            """)
        )

        with pytest.raises(
            (ComponentTreeException, dg.DagsterInvariantViolationError),
        ):
            with sandbox.load_component_and_build_defs(defs_path=defs_path):
                ...


def test_underscore_prefixed_py_file_is_not_loaded():
    """Files starting with '_' next to defs.yaml should be skipped (opt-out convention)."""
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            SimpleComponent,
            defs_yaml_contents={
                "type": _COMPONENT_TYPE,
                "attributes": {"asset_name": "component_asset"},
            },
        )

        # Write a private helper file that defines an asset — should not be auto-loaded
        (defs_path / "_private.py").write_text(
            textwrap.dedent("""\
                import dagster as dg

                @dg.asset
                def private_asset(): ...
            """)
        )

        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (_component, defs):
            asset_keys = {spec.key for spec in defs.get_all_asset_specs()}
            assert dg.AssetKey("component_asset") in asset_keys
            assert dg.AssetKey("private_asset") not in asset_keys
