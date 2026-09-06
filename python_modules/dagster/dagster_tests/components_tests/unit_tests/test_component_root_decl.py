"""Tests for ComponentRootLoc, ComponentRootDecl, and the unified root of
the component tree.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from dagster.components.core.component_tree import ComponentTree
from dagster.components.core.decl import ComponentRootDecl, DefsFolderDecl
from dagster.components.core.defs_module import (
    ComponentPath,
    ComponentRootComponent,
    ComponentRootLoc,
)
from dagster.components.testing.utils import create_defs_folder_sandbox


@pytest.fixture
def component_tree() -> Iterator[ComponentTree]:
    """A ComponentTree backed by a real on-disk defs module with one asset."""
    with create_defs_folder_sandbox() as sandbox:
        (sandbox.defs_folder_path / "asset.py").write_text(
            "import dagster as dg\n\n@dg.asset\ndef foo():\n    pass\n",
            encoding="utf-8",
        )
        with sandbox.build_component_tree() as tree:
            yield tree


class TestComponentRootLoc:
    def test_equality(self):
        assert ComponentRootLoc() == ComponentRootLoc()

    def test_distinct_from_component_path(self):
        assert ComponentRootLoc() != ComponentPath.from_path(Path("/tmp"))

    def test_without_instance_key(self):
        loc = ComponentRootLoc()
        assert loc.without_instance_key() == loc

    def test_display_key(self):
        assert ComponentRootLoc().get_display_key(Path("/fake")) == "<root>"


class TestComponentRootDecl:
    def test_find_root_decl_returns_component_root_decl(
        self, component_tree: ComponentTree
    ) -> None:
        root_decl = component_tree.find_root_decl()
        assert isinstance(root_decl, ComponentRootDecl)
        assert root_decl.loc == ComponentRootLoc()

    def test_root_decl_has_filesystem_child(self, component_tree: ComponentTree) -> None:
        root_decl = component_tree.find_root_decl()
        # In the no-UI subset there is exactly one child: the filesystem decl.
        assert len(root_decl.decls) == 1
        child = root_decl.decls[0]
        assert isinstance(child.loc, ComponentPath)
        assert isinstance(child, DefsFolderDecl)

    def test_iterate_loc_pairs_includes_root_and_children(
        self, component_tree: ComponentTree
    ) -> None:
        root_decl = component_tree.find_root_decl()
        pairs = dict(root_decl.iterate_loc_component_decl_pairs())
        assert ComponentRootLoc() in pairs
        # The filesystem decl loc should also appear in the iteration.
        fs_loc = ComponentPath.from_path(component_tree.defs_module_path)
        assert fs_loc in pairs

    def test_load_root_component_returns_component_root_component(
        self, component_tree: ComponentTree
    ) -> None:
        root = component_tree.load_root_component()
        assert isinstance(root, ComponentRootComponent)
        # The single child is the filesystem-loaded component.
        assert len(root.components) == 1

    def test_find_root_decl_filesystem_child_cached(self, component_tree: ComponentTree) -> None:
        """Two calls return root decls whose filesystem child is the same cached instance."""
        first = component_tree.find_root_decl()
        second = component_tree.find_root_decl()
        # Filesystem decl is cached, so child references the same object.
        assert first.decls[0] is second.decls[0]

    def test_build_defs_at_root_loc(self, component_tree: ComponentTree) -> None:
        """build_defs() with no args builds defs at ComponentRootLoc and merges children."""
        defs = component_tree.build_defs()
        keys = {spec.key.to_user_string() for spec in defs.resolve_all_asset_specs()}
        assert "foo" in keys
