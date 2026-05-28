"""Tests for ComponentTree integration with per-component UI definitions."""

import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import Mock

import dagster as dg
from dagster._core.instance_for_test import instance_for_test
from dagster._core.storage.defs_state.base import DefsStateStorage
from dagster._core.storage.defs_state.blob_storage_state_storage import UPathDefsStateStorage
from dagster.components.component.ui_definitions_state import (
    UIComponentEntry,
    write_ui_component_entry,
)
from dagster.components.core.component_tree import ComponentTree
from dagster.components.core.decl import ComponentRootDecl, UIDefinitionsDecl
from dagster.components.core.defs_module import ComponentPath, ComponentRootLoc, UIDefinitionsLoc
from dagster.components.testing.utils import create_defs_folder_sandbox
from dagster_shared import check


@contextmanager
def _instance_with_storage() -> Iterator[DefsStateStorage]:
    """Yield a DefsStateStorage backed by an instance configured for tests."""
    with tempfile.TemporaryDirectory() as state_dir:
        with instance_for_test(
            overrides={
                "defs_state_storage": {
                    "module": "dagster._core.storage.defs_state.blob_storage_state_storage",
                    "class": "UPathDefsStateStorage",
                    "config": {"base_path": state_dir},
                }
            }
        ) as instance:
            yield check.inst(instance.defs_state_storage, UPathDefsStateStorage)


@contextmanager
def _component_tree_for_loc(location_name: str | None) -> Iterator[ComponentTree]:
    """Build an empty-defs ComponentTree with the given code_location_name."""
    with create_defs_folder_sandbox() as sandbox:
        # An empty directory yields no filesystem decl; an __init__.py is
        # enough to give the root a single (no-op) child decl.
        (sandbox.defs_folder_path / "__init__.py").write_text("", encoding="utf-8")
        with sandbox.build_component_tree(code_location_name=location_name) as tree:
            yield tree


class TestUIDefinitionsLoc:
    def test_aggregate_loc_has_no_instance_key(self):
        assert UIDefinitionsLoc().instance_key is None

    def test_distinct_from_root(self):
        assert ComponentRootLoc() != UIDefinitionsLoc()

    def test_distinct_by_instance_key(self):
        assert UIDefinitionsLoc(instance_key="a") != UIDefinitionsLoc(instance_key="b")
        assert UIDefinitionsLoc() != UIDefinitionsLoc(instance_key="a")

    def test_without_instance_key_strips_id(self):
        assert UIDefinitionsLoc(instance_key="abc").without_instance_key() == UIDefinitionsLoc()

    def test_display_key_aggregate(self):
        assert UIDefinitionsLoc().get_display_key(Path("/fake")) == "<ui>"

    def test_display_key_with_instance(self):
        assert UIDefinitionsLoc(instance_key="abc").get_display_key(Path("/fake")) == "<ui>/abc"


class TestCodeLocationNamePlumbing:
    def test_explicit_code_location_name(self):
        tree = ComponentTree(
            defs_module=Mock(__name__="my_project.defs"),
            project_root=Path("/fake"),
            code_location_name="custom_location",
        )
        assert tree.code_location_name == "custom_location"

    def test_none_when_not_provided(self):
        tree = ComponentTree(
            defs_module=Mock(__name__="my_project.defs"),
            project_root=Path("/fake"),
        )
        assert tree.code_location_name is None


class TestRootDeclWithWrapper:
    def test_no_wrapper_when_no_code_location_name(self) -> None:
        """Without code_location_name, the UI subtree is omitted entirely."""
        with _instance_with_storage() as storage:
            write_ui_component_entry(
                storage,
                "other_loc",
                "comp1",
                UIComponentEntry(component_type="dagster.Component", attributes=""),
            )
            with _component_tree_for_loc(None) as tree:
                root = tree.find_root_decl()
                assert len(root.decls) == 1  # filesystem only
                assert isinstance(root.decls[0].loc, ComponentPath)

    def test_wrapper_present_with_no_components_when_storage_empty(self) -> None:
        """An empty UI subtree still gets a wrapper — gives the load path a
        consistent shape regardless of whether components exist yet.
        """
        with _instance_with_storage():
            with _component_tree_for_loc("test_loc") as tree:
                root = tree.find_root_decl()
                assert isinstance(root, ComponentRootDecl)
                assert len(root.decls) == 2
                ui_decl = root.decls[1]
                assert isinstance(ui_decl, UIDefinitionsDecl)
                assert ui_decl.location_name == "test_loc"
                assert ui_decl.children == []

    def test_wrapper_holds_each_ui_component_as_a_child(self) -> None:
        """Two UI components written → both appear as children of the wrapper,
        not as direct children of the root.
        """
        with _instance_with_storage() as storage:
            write_ui_component_entry(
                storage,
                "test_loc",
                "comp_a",
                UIComponentEntry(component_type="dagster.Component", attributes="k: a\n"),
            )
            write_ui_component_entry(
                storage,
                "test_loc",
                "comp_b",
                UIComponentEntry(component_type="dagster.Component", attributes="k: b\n"),
            )

            with _component_tree_for_loc("test_loc") as tree:
                root = tree.find_root_decl()
                # Root has filesystem + wrapper, no UI components hanging directly off root.
                assert len(root.decls) == 2
                ui_decl = check.inst(root.decls[1], UIDefinitionsDecl)
                assert len(ui_decl.children) == 2
                assert {c.entry.attributes for c in ui_decl.children} == {"k: a\n", "k: b\n"}

    def test_wrapper_filters_to_this_locations_components(self) -> None:
        """Components belonging to a different code location are filtered out."""
        with _instance_with_storage() as storage:
            write_ui_component_entry(
                storage,
                "test_loc",
                "mine",
                UIComponentEntry(component_type="dagster.Component", attributes=""),
            )
            write_ui_component_entry(
                storage,
                "other_loc",
                "not_mine",
                UIComponentEntry(component_type="dagster.Component", attributes=""),
            )

            with _component_tree_for_loc("test_loc") as tree:
                ui_decl = check.inst(tree.find_root_decl().decls[1], UIDefinitionsDecl)
                assert [c.loc for c in ui_decl.children] == [UIDefinitionsLoc(instance_key="mine")]

    def test_loc_pairs_iteration_includes_wrapper_and_each_child(self) -> None:
        with _instance_with_storage() as storage:
            write_ui_component_entry(
                storage,
                "test_loc",
                "comp_x",
                UIComponentEntry(component_type="dagster.Component", attributes=""),
            )
            with _component_tree_for_loc("test_loc") as tree:
                pairs = dict(tree.find_root_decl().iterate_loc_component_decl_pairs())
                # Root, wrapper, and the single UI component child all appear.
                assert ComponentRootLoc() in pairs
                assert UIDefinitionsLoc() in pairs
                assert UIDefinitionsLoc(instance_key="comp_x") in pairs


class TestPerComponentInvalidation:
    def test_each_ui_decl_registers_its_state_key(self) -> None:
        """Each child UIComponentDecl is registered against its own state key,
        so an invalidation of one component's key only affects that child.
        """
        with _instance_with_storage() as storage:
            write_ui_component_entry(
                storage,
                "test_loc",
                "comp_a",
                UIComponentEntry(component_type="dagster.Component", attributes=""),
            )
            write_ui_component_entry(
                storage,
                "test_loc",
                "comp_b",
                UIComponentEntry(component_type="dagster.Component", attributes=""),
            )

            with _component_tree_for_loc("test_loc") as tree:
                tree.find_root_decl()  # populate cache + register state keys

                tracker = tree.state_tracker
                tracker.set_cache_data(
                    UIDefinitionsLoc(instance_key="comp_a"), defs=dg.Definitions()
                )
                tracker.set_cache_data(
                    UIDefinitionsLoc(instance_key="comp_b"), defs=dg.Definitions()
                )

                tracker.invalidate_by_defs_state_key("dagster-ui-definitions[test_loc]/comp_a")

                assert tracker.get_cache_data(UIDefinitionsLoc(instance_key="comp_a")).defs is None
                assert (
                    tracker.get_cache_data(UIDefinitionsLoc(instance_key="comp_b")).defs is not None
                )

    def test_listing_picks_up_newly_added_components(self) -> None:
        """The list step is fresh on every find_root_decl call, so adding a new
        component after the first call is observed without explicit invalidation.
        """
        with _instance_with_storage() as storage:
            with _component_tree_for_loc("test_loc") as tree:
                first = tree.find_root_decl()
                ui_decl_first = check.inst(first.decls[1], UIDefinitionsDecl)
                assert ui_decl_first.children == []

                write_ui_component_entry(
                    storage,
                    "test_loc",
                    "new_comp",
                    UIComponentEntry(component_type="dagster.Component", attributes=""),
                )

                second = tree.find_root_decl()
                ui_decl_second = check.inst(second.decls[1], UIDefinitionsDecl)
                assert len(ui_decl_second.children) == 1
                assert ui_decl_second.children[0].loc == UIDefinitionsLoc(instance_key="new_comp")

    def test_per_component_decls_are_cached_across_calls(self) -> None:
        """An unchanged component's decl should be the same cached instance
        on a second find_root_decl call — that's the whole point of caching
        per-id rather than per-list.
        """
        with _instance_with_storage() as storage:
            write_ui_component_entry(
                storage,
                "test_loc",
                "stable",
                UIComponentEntry(component_type="dagster.Component", attributes=""),
            )
            with _component_tree_for_loc("test_loc") as tree:
                first = check.inst(tree.find_root_decl().decls[1], UIDefinitionsDecl)
                second = check.inst(tree.find_root_decl().decls[1], UIDefinitionsDecl)
                # Wrapper itself is freshly built each call (different list could differ),
                # but each child decl is cached and reused.
                assert first.children[0] is second.children[0]


class TestStorageListPrefix:
    """Smoke tests for the ``list_state_keys_with_prefix`` primitive on the base storage."""

    def test_default_impl_filters_global_state_info_in_memory(self) -> None:
        with _instance_with_storage() as storage:
            with tempfile.TemporaryDirectory() as tmp:
                p = Path(tmp) / "x"
                p.write_text("blob", encoding="utf-8")
                # Two unrelated keys + one matching prefix.
                storage.upload_state_from_path("UnrelatedFoo", "v1", p)
                storage.upload_state_from_path("UIDefinitions[loc]/abc", "v1", p)
                storage.upload_state_from_path("UIDefinitions[loc]/xyz", "v1", p)

                matches = sorted(storage.list_state_keys_with_prefix("UIDefinitions[loc]/"))
                assert matches == ["UIDefinitions[loc]/abc", "UIDefinitions[loc]/xyz"]

    def test_empty_when_no_state(self) -> None:
        with _instance_with_storage() as storage:
            assert storage.list_state_keys_with_prefix("UIDefinitions[loc]/") == []
