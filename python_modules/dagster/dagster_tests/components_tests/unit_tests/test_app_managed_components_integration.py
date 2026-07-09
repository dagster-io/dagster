"""Tests for ComponentTree integration with per-component app-managed components."""

import logging
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import Mock

import dagster as dg
from dagster._core.definitions.definitions_load_context import (
    DefinitionsLoadContext,
    DefinitionsLoadType,
)
from dagster._core.definitions.repository_definition.repository_definition import RepositoryLoadData
from dagster._core.instance_for_test import instance_for_test
from dagster._core.storage.defs_state.base import DefsStateStorage
from dagster._core.storage.defs_state.blob_storage_state_storage import UPathDefsStateStorage
from dagster.components.component.app_managed_state import (
    AppManagedComponentEntry,
    delete_app_managed_component_entry,
    write_app_managed_component_entry,
)
from dagster.components.core.component_tree import ComponentTree
from dagster.components.core.decl import AppManagedDefinitionsDecl, ComponentRootDecl
from dagster.components.core.defs_module import (
    AppManagedDefinitionsLoc,
    ComponentPath,
    ComponentRootLoc,
)
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


class TestAppManagedDefinitionsLoc:
    def test_aggregate_loc_has_no_instance_key(self):
        assert AppManagedDefinitionsLoc().instance_key is None

    def test_distinct_from_root(self):
        assert ComponentRootLoc() != AppManagedDefinitionsLoc()

    def test_distinct_by_instance_key(self):
        assert AppManagedDefinitionsLoc(instance_key="a") != AppManagedDefinitionsLoc(
            instance_key="b"
        )
        assert AppManagedDefinitionsLoc() != AppManagedDefinitionsLoc(instance_key="a")

    def test_without_instance_key_strips_id(self):
        assert (
            AppManagedDefinitionsLoc(instance_key="abc").without_instance_key()
            == AppManagedDefinitionsLoc()
        )

    def test_display_key_aggregate(self):
        assert AppManagedDefinitionsLoc().get_display_key(Path("/fake")) == "<ui>"

    def test_display_key_with_instance(self):
        assert (
            AppManagedDefinitionsLoc(instance_key="abc").get_display_key(Path("/fake"))
            == "<ui>/abc"
        )


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
            write_app_managed_component_entry(
                storage,
                "other_loc",
                "comp1",
                AppManagedComponentEntry(component_type="dagster.Component", attributes=""),
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
                assert isinstance(ui_decl, AppManagedDefinitionsDecl)
                assert ui_decl.location_name == "test_loc"
                assert ui_decl.children == []

    def test_wrapper_holds_each_app_managed_component_as_a_child(self) -> None:
        """Two UI components written → both appear as children of the wrapper,
        not as direct children of the root.
        """
        with _instance_with_storage() as storage:
            write_app_managed_component_entry(
                storage,
                "test_loc",
                "comp_a",
                AppManagedComponentEntry(component_type="dagster.Component", attributes="k: a\n"),
            )
            write_app_managed_component_entry(
                storage,
                "test_loc",
                "comp_b",
                AppManagedComponentEntry(component_type="dagster.Component", attributes="k: b\n"),
            )

            with _component_tree_for_loc("test_loc") as tree:
                root = tree.find_root_decl()
                # Root has filesystem + wrapper, no UI components hanging directly off root.
                assert len(root.decls) == 2
                ui_decl = check.inst(root.decls[1], AppManagedDefinitionsDecl)
                assert len(ui_decl.children) == 2
                assert {c.entry.attributes for c in ui_decl.children} == {"k: a\n", "k: b\n"}

    def test_wrapper_filters_to_this_locations_components(self) -> None:
        """Components belonging to a different code location are filtered out."""
        with _instance_with_storage() as storage:
            write_app_managed_component_entry(
                storage,
                "test_loc",
                "mine",
                AppManagedComponentEntry(component_type="dagster.Component", attributes=""),
            )
            write_app_managed_component_entry(
                storage,
                "other_loc",
                "not_mine",
                AppManagedComponentEntry(component_type="dagster.Component", attributes=""),
            )

            with _component_tree_for_loc("test_loc") as tree:
                ui_decl = check.inst(tree.find_root_decl().decls[1], AppManagedDefinitionsDecl)
                assert [c.loc for c in ui_decl.children] == [
                    AppManagedDefinitionsLoc(instance_key="mine")
                ]

    def test_loc_pairs_iteration_includes_wrapper_and_each_child(self) -> None:
        with _instance_with_storage() as storage:
            write_app_managed_component_entry(
                storage,
                "test_loc",
                "comp_x",
                AppManagedComponentEntry(component_type="dagster.Component", attributes=""),
            )
            with _component_tree_for_loc("test_loc") as tree:
                pairs = dict(tree.find_root_decl().iterate_loc_component_decl_pairs())
                # Root, wrapper, and the single UI component child all appear.
                assert ComponentRootLoc() in pairs
                assert AppManagedDefinitionsLoc() in pairs
                assert AppManagedDefinitionsLoc(instance_key="comp_x") in pairs


@contextmanager
def _ambient_location_name(
    location_name: str, storage: DefsStateStorage
) -> Iterator[DefinitionsLoadContext]:
    """Install a DefinitionsLoadContext reporting the given harness location name, pinned to
    the latest state versions in storage — mirrors how the gRPC server seeds the context.
    """
    with DefinitionsLoadContext.scoped(
        DefinitionsLoadContext(
            DefinitionsLoadType.INITIALIZATION,
            repository_load_data=RepositoryLoadData(
                defs_state_info=storage.get_latest_defs_state_info(),
                code_location_name=location_name,
            ),
        )
    ) as context:
        yield context


class TestAmbientLocationNameResolution:
    def test_ambient_name_used_when_tree_has_none(self) -> None:
        """A tree with no config-derived name (e.g. the legacy ``load_defs`` entry point)
        still discovers app-managed components when the harness reports the location name.
        """
        with _instance_with_storage() as storage:
            write_app_managed_component_entry(
                storage,
                "ambient_loc",
                "comp1",
                AppManagedComponentEntry(component_type="dagster.Component", attributes=""),
            )
            with _component_tree_for_loc(None) as tree:
                with _ambient_location_name("ambient_loc", storage):
                    root = tree.find_root_decl()
                    ui_decl = check.inst(root.decls[1], AppManagedDefinitionsDecl)
                    assert ui_decl.location_name == "ambient_loc"
                    assert [c.loc for c in ui_decl.children] == [
                        AppManagedDefinitionsLoc(instance_key="comp1")
                    ]

    def test_ambient_name_overrides_mismatched_config_name(self, caplog) -> None:
        """When the config-derived name disagrees with the harness-reported name, the
        harness name wins (it is what state keys were written under) and a warning is
        logged naming both.
        """
        with _instance_with_storage() as storage:
            write_app_managed_component_entry(
                storage,
                "ambient_loc",
                "ambient_comp",
                AppManagedComponentEntry(component_type="dagster.Component", attributes=""),
            )
            write_app_managed_component_entry(
                storage,
                "config_loc",
                "config_comp",
                AppManagedComponentEntry(component_type="dagster.Component", attributes=""),
            )
            with _component_tree_for_loc("config_loc") as tree:
                with _ambient_location_name("ambient_loc", storage):
                    with caplog.at_level(logging.WARNING):
                        ui_decl = check.inst(
                            tree.find_root_decl().decls[1], AppManagedDefinitionsDecl
                        )
            assert ui_decl.location_name == "ambient_loc"
            assert [c.loc for c in ui_decl.children] == [
                AppManagedDefinitionsLoc(instance_key="ambient_comp")
            ]
            assert "'config_loc'" in caplog.text
            assert "'ambient_loc'" in caplog.text

    def test_config_name_used_when_no_ambient_name(self) -> None:
        """Without a harness-reported name (e.g. dg CLI loads), the config-derived name
        on the tree is used, as before.
        """
        with _instance_with_storage() as storage:
            write_app_managed_component_entry(
                storage,
                "config_loc",
                "comp1",
                AppManagedComponentEntry(component_type="dagster.Component", attributes=""),
            )
            with _component_tree_for_loc("config_loc") as tree:
                ui_decl = check.inst(tree.find_root_decl().decls[1], AppManagedDefinitionsDecl)
                assert ui_decl.location_name == "config_loc"
                assert [c.loc for c in ui_decl.children] == [
                    AppManagedDefinitionsLoc(instance_key="comp1")
                ]

    def test_warns_when_state_exists_but_no_name_available(self, caplog) -> None:
        """App-managed state exists but neither the harness nor the project config provides
        a location name: discovery is skipped, but loudly rather than silently.
        """
        with _instance_with_storage() as storage:
            write_app_managed_component_entry(
                storage,
                "some_loc",
                "comp1",
                AppManagedComponentEntry(component_type="dagster.Component", attributes=""),
            )
            with _component_tree_for_loc(None) as tree:
                with caplog.at_level(logging.WARNING):
                    root = tree.find_root_decl()
                assert len(root.decls) == 1  # filesystem only, no app-managed wrapper
                assert "no app-managed components will be loaded" in caplog.text

    def test_no_warning_when_no_state_and_no_name(self, caplog) -> None:
        """The common case — no app-managed state anywhere, no location name — stays quiet."""
        with _instance_with_storage():
            with _component_tree_for_loc(None) as tree:
                with caplog.at_level(logging.WARNING):
                    root = tree.find_root_decl()
                assert len(root.decls) == 1
                assert "app-managed" not in caplog.text


class TestPerComponentInvalidation:
    def test_each_ui_decl_registers_its_state_key(self) -> None:
        """Each child AppManagedComponentDecl is registered against its own state key,
        so an invalidation of one component's key only affects that child.
        """
        with _instance_with_storage() as storage:
            write_app_managed_component_entry(
                storage,
                "test_loc",
                "comp_a",
                AppManagedComponentEntry(component_type="dagster.Component", attributes=""),
            )
            write_app_managed_component_entry(
                storage,
                "test_loc",
                "comp_b",
                AppManagedComponentEntry(component_type="dagster.Component", attributes=""),
            )

            with _component_tree_for_loc("test_loc") as tree:
                tree.find_root_decl()  # populate cache + register state keys

                tracker = tree.state_tracker
                tracker.set_cache_data(
                    AppManagedDefinitionsLoc(instance_key="comp_a"), defs=dg.Definitions()
                )
                tracker.set_cache_data(
                    AppManagedDefinitionsLoc(instance_key="comp_b"), defs=dg.Definitions()
                )

                tracker.invalidate_by_defs_state_key(
                    "dagster-app-managed-components[test_loc]/comp_a"
                )

                assert (
                    tracker.get_cache_data(AppManagedDefinitionsLoc(instance_key="comp_a")).defs
                    is None
                )
                assert (
                    tracker.get_cache_data(AppManagedDefinitionsLoc(instance_key="comp_b")).defs
                    is not None
                )

    def test_listing_picks_up_newly_added_components(self) -> None:
        """The list step is fresh on every find_root_decl call, so adding a new
        component after the first call is observed without explicit invalidation.
        """
        with _instance_with_storage() as storage:
            with _component_tree_for_loc("test_loc") as tree:
                first = tree.find_root_decl()
                ui_decl_first = check.inst(first.decls[1], AppManagedDefinitionsDecl)
                assert ui_decl_first.children == []

                write_app_managed_component_entry(
                    storage,
                    "test_loc",
                    "new_comp",
                    AppManagedComponentEntry(component_type="dagster.Component", attributes=""),
                )

                second = tree.find_root_decl()
                ui_decl_second = check.inst(second.decls[1], AppManagedDefinitionsDecl)
                assert len(ui_decl_second.children) == 1
                assert ui_decl_second.children[0].loc == AppManagedDefinitionsLoc(
                    instance_key="new_comp"
                )

    def test_per_component_decls_are_cached_across_calls(self) -> None:
        """An unchanged component's decl should be the same cached instance
        on a second find_root_decl call — that's the whole point of caching
        per-id rather than per-list.
        """
        with _instance_with_storage() as storage:
            write_app_managed_component_entry(
                storage,
                "test_loc",
                "stable",
                AppManagedComponentEntry(component_type="dagster.Component", attributes=""),
            )
            with _component_tree_for_loc("test_loc") as tree:
                first = check.inst(tree.find_root_decl().decls[1], AppManagedDefinitionsDecl)
                second = check.inst(tree.find_root_decl().decls[1], AppManagedDefinitionsDecl)
                # Wrapper itself is freshly built each call (different list could differ),
                # but each child decl is cached and reused.
                assert first.children[0] is second.children[0]


class TestDeletion:
    def test_delete_removes_component_from_root_decl(self) -> None:
        """After ``delete_app_managed_component_entry``, the next ``find_root_decl``
        call no longer includes the deleted component as a child of the
        UI wrapper — discovery is via fresh prefix-listing on each call.
        """
        with _instance_with_storage() as storage:
            write_app_managed_component_entry(
                storage,
                "test_loc",
                "comp_a",
                AppManagedComponentEntry(component_type="dagster.Component", attributes=""),
            )
            write_app_managed_component_entry(
                storage,
                "test_loc",
                "comp_b",
                AppManagedComponentEntry(component_type="dagster.Component", attributes=""),
            )

            with _component_tree_for_loc("test_loc") as tree:
                ui_decl = check.inst(tree.find_root_decl().decls[1], AppManagedDefinitionsDecl)
                assert {
                    check.inst(c.loc, AppManagedDefinitionsLoc).instance_key
                    for c in ui_decl.children
                } == {
                    "comp_a",
                    "comp_b",
                }

                delete_app_managed_component_entry(storage, "test_loc", "comp_a")

                ui_decl_after = check.inst(
                    tree.find_root_decl().decls[1], AppManagedDefinitionsDecl
                )
                assert [
                    check.inst(c.loc, AppManagedDefinitionsLoc).instance_key
                    for c in ui_decl_after.children
                ] == ["comp_b"]

    def test_delete_does_not_purge_surviving_siblings_cached_decl(self) -> None:
        """Deleting one component must not invalidate the cached decl of
        another — per-id caching means siblings are independent.
        """
        with _instance_with_storage() as storage:
            write_app_managed_component_entry(
                storage,
                "test_loc",
                "deleted",
                AppManagedComponentEntry(component_type="dagster.Component", attributes=""),
            )
            write_app_managed_component_entry(
                storage,
                "test_loc",
                "kept",
                AppManagedComponentEntry(component_type="dagster.Component", attributes=""),
            )

            with _component_tree_for_loc("test_loc") as tree:
                ui_decl = check.inst(tree.find_root_decl().decls[1], AppManagedDefinitionsDecl)
                kept_decl_first = next(
                    c
                    for c in ui_decl.children
                    if check.inst(c.loc, AppManagedDefinitionsLoc).instance_key == "kept"
                )

                delete_app_managed_component_entry(storage, "test_loc", "deleted")

                ui_decl_after = check.inst(
                    tree.find_root_decl().decls[1], AppManagedDefinitionsDecl
                )
                kept_decl_second = next(
                    c
                    for c in ui_decl_after.children
                    if check.inst(c.loc, AppManagedDefinitionsLoc).instance_key == "kept"
                )
                # Same cached object — sibling unaffected.
                assert kept_decl_first is kept_decl_second

    def test_delete_then_re_add_with_same_id_appears_again(self) -> None:
        """Delete + re-add at the same id round-trips through the tree."""
        with _instance_with_storage() as storage:
            write_app_managed_component_entry(
                storage,
                "test_loc",
                "comp1",
                AppManagedComponentEntry(component_type="dagster.Component", attributes="k: v1\n"),
            )

            with _component_tree_for_loc("test_loc") as tree:
                first = check.inst(tree.find_root_decl().decls[1], AppManagedDefinitionsDecl)
                assert first.children[0].entry.attributes == "k: v1\n"

                delete_app_managed_component_entry(storage, "test_loc", "comp1")

                gone = check.inst(tree.find_root_decl().decls[1], AppManagedDefinitionsDecl)
                assert gone.children == []

                # Re-add: write fresh state. The cached AppManagedComponentDecl from
                # before will get re-used unless its state key was invalidated;
                # callers that want to observe the new entry need to invalidate
                # explicitly via the state tracker (the writer-side concern).
                write_app_managed_component_entry(
                    storage,
                    "test_loc",
                    "comp1",
                    AppManagedComponentEntry(
                        component_type="dagster.Component", attributes="k: v2\n"
                    ),
                )
                tree.state_tracker.invalidate_loc(AppManagedDefinitionsLoc(instance_key="comp1"))

                back = check.inst(tree.find_root_decl().decls[1], AppManagedDefinitionsDecl)
                assert back.children[0].entry.attributes == "k: v2\n"


class TestStorageListPrefix:
    """Smoke tests for the ``list_state_keys_with_prefix`` primitive on the base storage."""

    def test_default_impl_filters_global_state_info_in_memory(self) -> None:
        with _instance_with_storage() as storage:
            with tempfile.TemporaryDirectory() as tmp:
                p = Path(tmp) / "x"
                p.write_text("blob", encoding="utf-8")
                # Two unrelated keys + one matching prefix.
                storage.upload_state_from_path("UnrelatedFoo", "v1", p)
                storage.upload_state_from_path("AppManagedDefinitions[loc]/abc", "v1", p)
                storage.upload_state_from_path("AppManagedDefinitions[loc]/xyz", "v1", p)

                matches = sorted(storage.list_state_keys_with_prefix("AppManagedDefinitions[loc]/"))
                assert matches == [
                    "AppManagedDefinitions[loc]/abc",
                    "AppManagedDefinitions[loc]/xyz",
                ]

    def test_empty_when_no_state(self) -> None:
        with _instance_with_storage() as storage:
            assert storage.list_state_keys_with_prefix("AppManagedDefinitions[loc]/") == []
